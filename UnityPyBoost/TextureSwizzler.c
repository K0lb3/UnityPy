#include <TextureSwizzler.h>

const uint32_t GOB_X_BLOCK_COUNT = 4;
const uint32_t GOB_Y_BLOCK_COUNT = 8;
const uint32_t BLOCKS_IN_GOB = 32; // GOB_X_BLOCK_COUNT * GOB_Y_BLOCK_COUNT;

const uint32_t GOB_MAP[32][2] = {{0, 0}, {0, 1}, {1, 0}, {1, 1}, {0, 2}, {0, 3}, {1, 2}, {1, 3}, {0, 4}, {0, 5}, {1, 4}, {1, 5}, {0, 6}, {0, 7}, {1, 6}, {1, 7}, {2, 0}, {2, 1}, {3, 0}, {3, 1}, {2, 2}, {2, 3}, {3, 2}, {3, 3}, {2, 4}, {2, 5}, {3, 4}, {3, 5}, {2, 6}, {2, 7}, {3, 6}, {3, 7}};

PyObject *switch_deswizzle(PyObject *self, PyObject *args)
{
    // define vars
    uint8_t *src_data;
    Py_ssize_t data_size;
    uint32_t pixel_width;

    uint32_t width;
    uint32_t height;
    uint32_t block_width;
    uint32_t block_height;
    uint32_t gobs_per_block;

    if (!PyArg_ParseTuple(args, "y#IIIIII", &src_data, &data_size, &pixel_width, &width, &height, &block_width, &block_height, &gobs_per_block))
        return NULL;

    char *dst_data = (char *)malloc(data_size);

    uint32_t block_count_x = width / block_width;
    uint32_t block_count_y = height / block_height;

    uint32_t gob_count_x = block_count_x / GOB_X_BLOCK_COUNT;
    uint32_t gob_count_y = block_count_y / GOB_Y_BLOCK_COUNT;

    uint32_t src_x = 0;
    uint32_t src_y = 0;

    uint32_t block_pixel_width = block_width * pixel_width;
    uint32_t row_pixel_width = width * pixel_width;

    uint32_t gob_x, gob_y, gob_dst_x, gob_dst_y, src_offset, dst_offset;

    for (uint32_t y = 0; y < gob_count_y; y++)
    {
        for (uint32_t x = 0; x < gob_count_x; x++)
        {
            for (uint32_t k = 0; k < gobs_per_block; k++)
            {
                for (uint32_t l = 0; l < BLOCKS_IN_GOB; l++)
                {
                    // printf("%d/%d, %d/%d, %d/%d, %d/%d\n", y, gob_count_y, x, gob_count_x, k, gobs_per_block, l, gobs_per_block);
                    gob_x = ((l >> 3) & 0b10) | ((l >> 1) & 0b1);
                    gob_y = ((l >> 1) & 0b110) | (l & 0b1);
                    gob_dst_x = x * GOB_X_BLOCK_COUNT + gob_x;
                    gob_dst_y = (y * gobs_per_block + k) * GOB_Y_BLOCK_COUNT + gob_y;

                    src_offset = (src_x * block_width + (src_y * block_height) * width) * pixel_width;
                    dst_offset = (gob_dst_x * block_width + (gob_dst_y * block_height) * width) * pixel_width;

                    for (uint32_t by = 0; by < block_height; by++)
                    {
                        if ((dst_offset > data_size) || (src_offset > data_size))
                        {
                            break;
                        }
                        uint32_t copy_width = block_pixel_width;
                        if ((data_size - src_offset) < block_pixel_width)
                        {
                            copy_width = data_size - src_offset;
                        }
                        else if ((data_size - dst_offset) < block_pixel_width)
                        {
                            copy_width = data_size - dst_offset;
                        }

                        memcpy(
                            dst_data + dst_offset,
                            src_data + src_offset,
                            copy_width);
                        src_offset += row_pixel_width;
                        dst_offset += row_pixel_width;
                    }
                    src_x += 1;
                    if (src_x >= block_count_x)
                    {
                        src_x = 0;
                        src_y += 1;
                    }
                }
            }
        }
    }

    PyObject *ret = PyBytes_FromStringAndSize(dst_data, data_size);
    free(dst_data);

    return ret;
}
