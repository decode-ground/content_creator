import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";
import { authApi, ApiError } from "@/lib/api";

export function useAuth() {
  const queryClient = useQueryClient();

  const meQuery = useQuery({
    queryKey: ["auth", "me"],
    queryFn: authApi.me,
    retry: false,
    refetchOnWindowFocus: false,
  });

  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    },
  });

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    },
  });

  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      queryClient.setQueryData(["auth", "me"], null);
    },
  });

  const register = useCallback(
    async (email: string, password: string, name: string) => {
      return registerMutation.mutateAsync({ email, password, name });
    },
    [registerMutation]
  );

  const login = useCallback(
    async (email: string, password: string) => {
      return loginMutation.mutateAsync({ email, password });
    },
    [loginMutation]
  );

  const logout = useCallback(async () => {
    try {
      await logoutMutation.mutateAsync();
    } catch (error: unknown) {
      if (error instanceof ApiError && error.status === 401) {
        return;
      }
      throw error;
    } finally {
      queryClient.setQueryData(["auth", "me"], null);
      await queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    }
  }, [logoutMutation, queryClient]);

  const state = useMemo(() => {
    return {
      user: meQuery.data ?? null,
      loading:
        meQuery.isLoading ||
        registerMutation.isPending ||
        loginMutation.isPending ||
        logoutMutation.isPending,
      error:
        meQuery.error ??
        registerMutation.error ??
        loginMutation.error ??
        logoutMutation.error ??
        null,
      isAuthenticated: Boolean(meQuery.data),
    };
  }, [
    meQuery.data,
    meQuery.error,
    meQuery.isLoading,
    registerMutation.error,
    registerMutation.isPending,
    loginMutation.error,
    loginMutation.isPending,
    logoutMutation.error,
    logoutMutation.isPending,
  ]);

  return {
    ...state,
    refresh: () => meQuery.refetch(),
    register,
    login,
    logout,
  };
}
