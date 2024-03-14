#include "llvm-c/Target.h"
#include "llvm/ADT/StringExtras.h"
#include "llvm/MC/MCContext.h"
#include "llvm/MC/MCDisassembler/MCDisassembler.h"
#include "llvm/MC/TargetRegistry.h"
#include "llvm/Object/ELFObjectFile.h"
#include "llvm/Object/ELFTypes.h"
#include "llvm/Object/ObjectFile.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/Support/Errc.h"
#include "llvm/Support/WithColor.h"
#include "llvm/Target/TargetMachine.h"

using namespace llvm;

static cl::opt<std::string>
    InputFilename(cl::Positional, cl::desc("Input object file"), cl::init("-"));

static ExitOnError ExitOnErr("opcode_from_object_file error: ");

int main(int argc, char **argv) {
  cl::ParseCommandLineOptions(argc, argv, "llvm-tokenizer\n");

  object::OwningBinary<object::Binary> ObjBinary =
      ExitOnErr(object::createBinary(InputFilename));
  object::Binary &Binary = *ObjBinary.getBinary();
  object::ObjectFile *Obj = cast<object::ObjectFile>(&Binary);

  LLVMInitializeX86Target();
  LLVMInitializeX86TargetInfo();
  LLVMInitializeX86TargetMC();
  LLVMInitializeX86AsmPrinter();
  LLVMInitializeX86Disassembler();
  LLVMInitializeX86AsmParser();

  std::string LookupError;
  const llvm::Target *const LLVMTarget =
      llvm::TargetRegistry::lookupTarget("x86_64", LookupError);

  if (LLVMTarget == nullptr)
    ExitOnErr(llvm::make_error<StringError>(llvm::errc::invalid_argument,
                                            "Bad triple"));

  TargetOptions LLVMTargetOptions;
  std::unique_ptr<TargetMachine> LLVMTargetMachine(
      LLVMTarget->createTargetMachine("x86_64", "", "", LLVMTargetOptions,
                                      std::nullopt));
  std::unique_ptr<MCContext> LLVMMCContext = std::make_unique<MCContext>(
      LLVMTargetMachine->getTargetTriple(), LLVMTargetMachine->getMCAsmInfo(),
      LLVMTargetMachine->getMCRegisterInfo(),
      LLVMTargetMachine->getMCSubtargetInfo());
  std::unique_ptr<MCDisassembler> LLVMMCDisassembler(
      LLVMTarget->createMCDisassembler(*LLVMTargetMachine->getMCSubtargetInfo(),
                                       *LLVMMCContext));

  for (const auto &Section : Obj->sections()) {
    if (!Section.isText())
      continue;

    StringRef SectionContents = ExitOnErr(Section.getContents());
    ArrayRef<uint8_t> SectionContentsData(
        reinterpret_cast<const uint8_t *>(SectionContents.data()),
        SectionContents.size());

    MCInst CurrentInstruction;
    uint64_t InstructionSize;
    const uint64_t InstructionAddress =
        reinterpret_cast<uint64_t>(SectionContentsData.data());
    std::string DisassemblerOutputBuffer;
    llvm::raw_string_ostream Output(DisassemblerOutputBuffer);

    const MCDisassembler::DecodeStatus Status =
        LLVMMCDisassembler->getInstruction(CurrentInstruction, InstructionSize,
                                           SectionContentsData,
                                           InstructionAddress, Output);

    if (Status != MCDisassembler::DecodeStatus::Success)
      ExitOnErr(make_error<StringError>(llvm::errc::invalid_argument,
                                        "Failed to disassemble code"));

    dbgs() << CurrentInstruction.getOpcode() << "\n";

    // We should only have one text section, so just break when we find it.
    break;
  }

  return 0;
}
