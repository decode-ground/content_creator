/**
 * Data API placeholder
 *
 * This module previously used Manus Forge API for external data services.
 * Replace with your own API integrations as needed.
 */

export type DataApiCallOptions = {
  query?: Record<string, unknown>;
  body?: Record<string, unknown>;
  pathParams?: Record<string, unknown>;
  formData?: Record<string, unknown>;
};

export async function callDataApi(
  apiId: string,
  _options: DataApiCallOptions = {}
): Promise<unknown> {
  console.warn(
    "[Data API] Data API service is not configured.",
    { apiId }
  );

  throw new Error(
    "Data API service is not configured. This feature requires an external API integration."
  );
}
