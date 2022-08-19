// check if the system is little endian
#define IS_LITTLE_ENDIAN (*(unsigned char *)&(unsigned short){1})

// set swap funcions (source: old version of nodejs/src/node_buffer.cc)
#if defined(__GNUC__) || defined(__clang__)
#define bswap16(x) __builtin_bswap16(x)
#define bswap32(x) __builtin_bswap32(x)
#define bswap64(x) __builtin_bswap64(x)
#elif defined(__linux__)
#include <byteswap.h>
#define bswap16(x) bswap_16(x)
#define bswap32(x) bswap_32(x)
#define bswap64(x) bswap_64(x)
#elif defined(_MSC_VER)
#include <intrin.h>
#define bswap16(x) _byteswap_ushort(x)
#define bswap32(x) _byteswap_ulong(x)
#define bswap64(x) _byteswap_uint64(x)
#else
#define bswap16 ((x) << 8) | ((x) >> 8)
#define bswap32                 \
    (((x)&0xFF) << 24) |        \
        (((x)&0xFF00) << 8) |   \
        (((x) >> 8) & 0xFF00) | \
        (((x) >> 24) & 0xFF)
#define bswap64                               \
    (((x)&0xFF00000000000000ull) >> 56) |     \
        (((x)&0x00FF000000000000ull) >> 40) | \
        (((x)&0x0000FF0000000000ull) >> 24) | \
        (((x)&0x000000FF00000000ull) >> 8) |  \
        (((x)&0x00000000FF000000ull) << 8) |  \
        (((x)&0x0000000000FF0000ull) << 24) | \
        (((x)&0x000000000000FF00ull) << 40) | \
        (((x)&0x00000000000000FFull) << 56)
#endif