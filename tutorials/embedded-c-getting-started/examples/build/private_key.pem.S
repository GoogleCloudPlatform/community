/* * Data converted from /Users/galzahavi/Desktop/GCP/community/tutorials/embedded-c-getting-started/examples/main/certs/private_key.pem
 * (null byte appended)
 */
.data
.section .rodata.embedded

.global private_key_pem
private_key_pem:

.global _binary_private_key_pem_start
_binary_private_key_pem_start: /* for objcopy compatibility */
.byte 0x00

.global _binary_private_key_pem_end
_binary_private_key_pem_end: /* for objcopy compatibility */


.global private_key_pem_length
private_key_pem_length: /* not including null byte */
.word 0
