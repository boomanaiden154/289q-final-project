#include "llvm-c/Target.h"
#include "llvm/MC/MCContext.h"
#include "llvm/MC/MCDisassembler/MCDisassembler.h"
#include "llvm/MC/MCSubtargetInfo.h"
#include "llvm/MC/TargetRegistry.h"
#include "llvm/Support/Debug.h"
#include "llvm/Support/Errc.h"
#include "llvm/Support/Error.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Target/TargetMachine.h"
#include "llvm/Target/TargetOptions.h"

using namespace llvm;

// TODO(boomanaiden154): Add facilities to parse basic blocks from hex values
// TODO(boomanaiden154): Add facilities for loading uops.info information.
// TODO(boomanaiden154): Add facilities for setting up ILP constraints.

constexpr int kInvalidHexDigit = 256;

int ParseHexDigit(char digit) {
  if (digit >= '0' && digit <= '9') {
    return digit - '0';
  }
  if (digit >= 'a' && digit <= 'f') {
    return digit - 'a' + 10;
  }
  if (digit >= 'A' && digit <= 'F') {
    return digit - 'A' + 10;
  }
  return kInvalidHexDigit;
}

bool IsAsciiWhitespace(char c) {
  return c == ' ' || c == '\t' || c == '\r' || c == '\n';
}

Expected<std::vector<uint8_t>> ParseHexString(std::string_view hex_string) {
  if (hex_string.size() % 2 != 0) {
    return llvm::make_error<StringError>(llvm::errc::invalid_argument,
                                         "Hex string is invalid length");
  }
  std::vector<uint8_t> res;
  while (!hex_string.empty()) {
    const int hex_value =
        (ParseHexDigit(hex_string[0]) << 4) + ParseHexDigit(hex_string[1]);
    if (hex_value >= 256) {
      return llvm::make_error<StringError>(llvm::errc::invalid_argument,
                                           "Hex string is invalid");
    }
    res.push_back(hex_value);
    hex_string.remove_prefix(2);
  }

  return res;
}

Expected<std::vector<MCInst>>
disassembleInstructions(ArrayRef<uint8_t> MachineCode,
                        std::unique_ptr<MCDisassembler> &LLVMMCDisassembler) {
  std::vector<MCInst> DisassembledInstructions;
  while (!MachineCode.empty()) {
    MCInst CurrentInstruction;
    uint64_t InstructionSize;
    const uint64_t InstructionAddress =
        reinterpret_cast<uint64_t>(MachineCode.data());
    std::string DisassemblerOutputBuffer;
    llvm::raw_string_ostream Output(DisassemblerOutputBuffer);

    const MCDisassembler::DecodeStatus Status =
        LLVMMCDisassembler->getInstruction(CurrentInstruction, InstructionSize,
                                           MachineCode, InstructionAddress,
                                           Output);

    if (Status != MCDisassembler::DecodeStatus::Success)
      return make_error<StringError>(llvm::errc::invalid_argument,
                                     "Failed to disassemble code");

    MachineCode = MachineCode.drop_front(InstructionSize);
  }
  return DisassembledInstructions;
}

static ExitOnError ExitOnErr("generate_ilp_from_bbs error: ");

int main() {
  std::vector<uint8_t> HexValues =
      ExitOnErr(ParseHexString("4889de4889c24c89ff"));

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

  std::vector<MCInst> Instructions =
      ExitOnErr(disassembleInstructions(HexValues, LLVMMCDisassembler));

  dbgs() << "Hello World\n";
}
