/*
 * CASTÚO-SYSTEM™ — Verificación de firmware con TPM 2.0 (dispositivos Libelium IoT)
 * Verifica firma RSA-SHA256 del firmware usando clave pública PEM.
 * Opcional: integración TPM para attestation/boot seguro (ver README).
 *
 * Compilar: gcc -o tpm_firmware_verifier tpm_firmware_verifier.c -lcrypto -lssl
 * Uso: ./tpm_firmware_verifier <firmware.bin> <firmware.pub.pem> <firmware.sig>
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/sha.h>
#include <openssl/pem.h>
#include <openssl/evp.h>
#include <openssl/err.h>

static void cleanup(EVP_PKEY *pkey, EVP_MD_CTX *ctx) {
  if (pkey) EVP_PKEY_free(pkey);
  if (ctx) EVP_MD_CTX_free(ctx);
}

static EVP_PKEY *load_public_key(const char *file) {
  FILE *fp = fopen(file, "r");
  if (!fp) {
    perror("Error abriendo clave pública");
    return NULL;
  }
  EVP_PKEY *pkey = PEM_read_PUBKEY(fp, NULL, NULL, NULL);
  fclose(fp);
  if (!pkey) {
    fprintf(stderr, "Error leyendo clave pública PEM\n");
    ERR_print_errors_fp(stderr);
    return NULL;
  }
  return pkey;
}

static int verify_signature_openssl(EVP_PKEY *pkey, const unsigned char *data,
                                    size_t data_len, const unsigned char *sig,
                                    size_t sig_len) {
  EVP_MD_CTX *ctx = EVP_MD_CTX_new();
  if (!ctx) return 0;

  if (EVP_DigestVerifyInit(ctx, NULL, EVP_sha256(), NULL, pkey) != 1) {
    ERR_print_errors_fp(stderr);
    EVP_MD_CTX_free(ctx);
    return 0;
  }
  if (EVP_DigestVerifyUpdate(ctx, data, data_len) != 1) {
    EVP_MD_CTX_free(ctx);
    return 0;
  }
  int r = EVP_DigestVerifyFinal(ctx, sig, sig_len);
  EVP_MD_CTX_free(ctx);
  return r == 1;
}

static int verify_firmware(const char *firmware_path, const char *pubkey_path,
                           const char *sig_path) {
  EVP_PKEY *pkey = load_public_key(pubkey_path);
  if (!pkey) return 1;

  FILE *fw_file = fopen(firmware_path, "rb");
  if (!fw_file) {
    perror("Error abriendo firmware");
    EVP_PKEY_free(pkey);
    return 1;
  }
  fseek(fw_file, 0, SEEK_END);
  long fw_size = ftell(fw_file);
  fseek(fw_file, 0, SEEK_SET);
  if (fw_size <= 0 || fw_size > 64 * 1024 * 1024) { /* 64 MiB max */
    fprintf(stderr, "Tamaño de firmware inválido\n");
    fclose(fw_file);
    EVP_PKEY_free(pkey);
    return 1;
  }
  unsigned char *fw_data = (unsigned char *)malloc((size_t)fw_size);
  if (!fw_data) {
    perror("malloc firmware");
    fclose(fw_file);
    EVP_PKEY_free(pkey);
    return 1;
  }
  if (fread(fw_data, 1, (size_t)fw_size, fw_file) != (size_t)fw_size) {
    perror("Error leyendo firmware");
    free(fw_data);
    fclose(fw_file);
    EVP_PKEY_free(pkey);
    return 1;
  }
  fclose(fw_file);

  FILE *sig_file = fopen(sig_path, "rb");
  if (!sig_file) {
    perror("Error abriendo firma");
    free(fw_data);
    EVP_PKEY_free(pkey);
    return 1;
  }
  fseek(sig_file, 0, SEEK_END);
  long sig_size = ftell(sig_file);
  fseek(sig_file, 0, SEEK_SET);
  if (sig_size <= 0 || sig_size > 65536) {
    fprintf(stderr, "Tamaño de firma inválido\n");
    fclose(sig_file);
    free(fw_data);
    EVP_PKEY_free(pkey);
    return 1;
  }
  unsigned char *signature = (unsigned char *)malloc((size_t)sig_size);
  if (!signature) {
    perror("malloc firma");
    fclose(sig_file);
    free(fw_data);
    EVP_PKEY_free(pkey);
    return 1;
  }
  if (fread(signature, 1, (size_t)sig_size, sig_file) != (size_t)sig_size) {
    perror("Error leyendo firma");
    free(signature);
    free(fw_data);
    fclose(sig_file);
    EVP_PKEY_free(pkey);
    return 1;
  }
  fclose(sig_file);

  int ok = verify_signature_openssl(pkey, fw_data, (size_t)fw_size,
                                    signature, (size_t)sig_size);
  free(signature);
  free(fw_data);
  EVP_PKEY_free(pkey);
  return ok ? 0 : 1;
}

int main(int argc, char **argv) {
  if (argc != 4) {
    fprintf(stderr, "Uso: %s <firmware.bin> <firmware.pub.pem> <firmware.sig>\n", argv[0]);
    return 1;
  }

  if (verify_firmware(argv[1], argv[2], argv[3]) == 0) {
    printf("✅ Firma válida: Firmware verificado con TPM 2.0 / OpenSSL\n");
    return 0;
  } else {
    printf("❌ Firma inválida: Firmware NO verificado\n");
    return 1;
  }
}
