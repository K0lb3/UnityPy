#if __cplusplus >= 202101L // "C++23";
#include <bit>
#define bswap16(x) std::byteswap<uint16_t>(x)
#define bswap32(x) std::byteswap<uint32_t>(x)
#define bswap64(x) std::byteswap<uint64_t>(x)
#else
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
#ifdef __builtin_bswap16
#define bswap16(x) __builtin_bswap16(x)
#else
#define bswap16 ((x) << 8) | ((x) >> 8)
#endif
#ifdef __builtin_bswap32
#define bswap32(x) __builtin_bswap32(x)
#else
#define bswap32                 \
    (((x) & 0xFF) << 24) |      \
        (((x) & 0xFF00) << 8) | \
        (((x) >> 8) & 0xFF00) | \
        (((x) >> 24) & 0xFF)
#endif
#ifdef __builtin_bswap64
#define bswap64 __builtin_bswap64(x)
#else
#define bswap64                                 \
    (((x) & 0xFF00000000000000ull) >> 56) |     \
        (((x) & 0x00FF000000000000ull) >> 40) | \
        (((x) & 0x0000FF0000000000ull) >> 24) | \
        (((x) & 0x000000FF00000000ull) >> 8) |  \
        (((x) & 0x00000000FF000000ull) << 8) |  \
        (((x) & 0x0000000000FF0000ull) << 24) | \
        (((x) & 0x000000000000FF00ull) << 40) | \
        (((x) & 0x00000000000000FFull) << 56)
#endif
#endif
#endif

template<typename T>
inline void swap_any_inplace(T *x)
{
    if constexpr (sizeof(T) == 1)
    {
        // do nothing
    }
    else if constexpr (sizeof(T) == 2)
    {

        *(uint16_t *)x = bswap16(*(uint16_t *)x);
    }
    else if constexpr (sizeof(T) == 4)
    {
        *(uint32_t *)x = bswap32(*(uint32_t *)x);
    }
    else if constexpr (sizeof(T) == 8)
    {
        *(uint64_t *)x = bswap64(*(uint64_t *)x);
    }
    else
    {
        // gcc is tripping and somehow reaching this at compile time
        // static_assert(false, "Swap not implemented for this size");
    }
}
