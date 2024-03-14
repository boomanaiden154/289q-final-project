#include "llvm/Support/Debug.h"
#include "llvm/Support/Errc.h"
#include "llvm/Support/Error.h"
#include "llvm/Support/raw_ostream.h"

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

static ExitOnError ExitOnErr("generate_ilp_from_bbs error: ");

int main() {
  std::vector<uint8_t> HexValues =
      ExitOnErr(ParseHexString("4889de4889c24c89ff"));
  dbgs() << "Hello World\n";
}
