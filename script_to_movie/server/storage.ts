/**
 * Storage helpers - placeholder implementation
 *
 * This module provides stub implementations for storage operations.
 * Replace with AWS S3 or another storage service in the future.
 */

export async function storagePut(
  relKey: string,
  _data: Buffer | Uint8Array | string,
  _contentType = "application/octet-stream"
): Promise<{ key: string; url: string }> {
  console.warn(
    "[Storage] Storage service is not configured. Returning placeholder.",
    { key: relKey }
  );

  return {
    key: relKey,
    url: `https://placehold.co/1024x1024/2a2a2a/white?text=Storage+Not+Configured`,
  };
}

export async function storageGet(
  relKey: string
): Promise<{ key: string; url: string }> {
  console.warn(
    "[Storage] Storage service is not configured. Returning placeholder.",
    { key: relKey }
  );

  return {
    key: relKey,
    url: `https://placehold.co/1024x1024/2a2a2a/white?text=Storage+Not+Configured`,
  };
}
