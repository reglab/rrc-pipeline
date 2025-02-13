// This file is auto-generated by @hey-api/openapi-ts

import {
  type Options,
  createClient,
  createConfig,
} from "@hey-api/client-fetch";
import {
  type CreateProxyPatternData,
  type CreateProxyPatternError,
  type CreateProxyPatternResponse,
  CreateProxyPatternResponseTransformer,
  type DeleteProxyPatternData,
  type DeleteProxyPatternError,
  type DeleteProxyPatternResponse,
  type ListProxyPatternsError,
  type ListProxyPatternsResponse,
  ListProxyPatternsResponseTransformer,
  type ReadProxyPatternData,
  type ReadProxyPatternError,
  type ReadProxyPatternResponse,
  ReadProxyPatternResponseTransformer,
  type UpdateProxyPatternData,
  type UpdateProxyPatternError,
  type UpdateProxyPatternResponse,
  UpdateProxyPatternResponseTransformer,
} from "./types.gen";

export const client = createClient(createConfig());

export class DefaultService {
  /**
   * List Proxy Patterns
   */
  public static listProxyPatterns<ThrowOnError extends boolean = false>(
    options?: Options<unknown, ThrowOnError>,
  ) {
    return (options?.client ?? client).get<
      ListProxyPatternsResponse,
      ListProxyPatternsError,
      ThrowOnError
    >({
      ...options,
      url: "/proxy_patterns",
      responseTransformer: ListProxyPatternsResponseTransformer,
    });
  }

  /**
   * Create Proxy Pattern
   */
  public static createProxyPattern<ThrowOnError extends boolean = false>(
    options: Options<CreateProxyPatternData, ThrowOnError>,
  ) {
    return (options?.client ?? client).post<
      CreateProxyPatternResponse,
      CreateProxyPatternError,
      ThrowOnError
    >({
      ...options,
      url: "/proxy_patterns",
      responseTransformer: CreateProxyPatternResponseTransformer,
    });
  }

  /**
   * Read Proxy Pattern
   */
  public static readProxyPattern<ThrowOnError extends boolean = false>(
    options: Options<ReadProxyPatternData, ThrowOnError>,
  ) {
    return (options?.client ?? client).get<
      ReadProxyPatternResponse,
      ReadProxyPatternError,
      ThrowOnError
    >({
      ...options,
      url: "/proxy_patterns/{pattern_id}",
      responseTransformer: ReadProxyPatternResponseTransformer,
    });
  }

  /**
   * Update Proxy Pattern
   */
  public static updateProxyPattern<ThrowOnError extends boolean = false>(
    options: Options<UpdateProxyPatternData, ThrowOnError>,
  ) {
    return (options?.client ?? client).patch<
      UpdateProxyPatternResponse,
      UpdateProxyPatternError,
      ThrowOnError
    >({
      ...options,
      url: "/proxy_patterns/{pattern_id}",
      responseTransformer: UpdateProxyPatternResponseTransformer,
    });
  }

  /**
   * Delete Proxy Pattern
   */
  public static deleteProxyPattern<ThrowOnError extends boolean = false>(
    options: Options<DeleteProxyPatternData, ThrowOnError>,
  ) {
    return (options?.client ?? client).delete<
      DeleteProxyPatternResponse,
      DeleteProxyPatternError,
      ThrowOnError
    >({
      ...options,
      url: "/proxy_patterns/{pattern_id}",
    });
  }
}
