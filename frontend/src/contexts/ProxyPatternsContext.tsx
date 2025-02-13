import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { createContext, useContext, ReactNode } from "react";
import { DefaultService } from "../client";
import {
  listProxyPatternsOptions,
  listProxyPatternsQueryKey,
} from "../client/@tanstack/react-query.gen";
import {
  ProxyPatternCreate,
  ProxyPatternRead,
  ProxyPatternUpdate,
} from "../client/types.gen";

interface ProxyPatternsContextType {
  proxyPatterns: ProxyPatternRead[];
  createPattern: (
    patternCreate: ProxyPatternCreate,
  ) => Promise<ProxyPatternRead>;
  updatePattern: ({
    patternId,
    patternUpdate,
  }: {
    patternId: number;
    patternUpdate: ProxyPatternUpdate;
  }) => Promise<ProxyPatternRead>;
  deletePattern: (patternId: number) => Promise<void>;
}

const ProxyPatternsContext = createContext<ProxyPatternsContextType | null>(
  null,
);

export const ProxyPatternsProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const queryClient = useQueryClient();

  const { data: proxyPatterns = [] } = useQuery(listProxyPatternsOptions());

  const { mutateAsync: createPattern } = useMutation({
    mutationFn: async (patternCreate: ProxyPatternCreate) => {
      const { data: createdPattern } = await DefaultService.createProxyPattern({
        body: patternCreate,
      });
      return createdPattern;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listProxyPatternsQueryKey() });
    },
  });

  const { mutateAsync: updatePattern } = useMutation({
    mutationFn: async ({
      patternId,
      patternUpdate,
    }: {
      patternId: number;
      patternUpdate: ProxyPatternUpdate;
    }) => {
      const { data: updatedPattern } = await DefaultService.updateProxyPattern({
        body: patternUpdate,
        path: {
          pattern_id: patternId,
        },
      });
      return updatedPattern;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listProxyPatternsQueryKey(),
      });
    },
  });

  const { mutateAsync: deletePattern } = useMutation({
    mutationFn: async (patternId: number) => {
      await DefaultService.deleteProxyPattern({
        path: { pattern_id: patternId },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listProxyPatternsQueryKey() });
    },
  });

  return (
    <ProxyPatternsContext.Provider
      value={{
        proxyPatterns,
        createPattern,
        updatePattern,
        deletePattern,
      }}
    >
      {children}
    </ProxyPatternsContext.Provider>
  );
};

export const useProxyPatterns = () => {
  const context = useContext(ProxyPatternsContext);
  if (!context) {
    throw new Error(
      "useProxyPatterns must be used within a ProxyPatternsProvider",
    );
  }
  return context;
};
