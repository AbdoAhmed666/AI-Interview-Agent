"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { toast } from "sonner";

import { useAuth } from "@/contexts/AuthContext";

import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Input from "@/components/ui/Input";
import SectionTitle from "@/components/ui/SectionTitle";

import Link from "next/link";

import {
  loginSchema,
  LoginFormData,
} from "@/lib/validation";

export default function LoginPage() {

  const router = useRouter();

  const { login } = useAuth();

  const [loading, setLoading] =
    useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  async function onSubmit(
    data: LoginFormData
  ) {
    try {

      setLoading(true);

      await login(data);

      toast.success("Welcome back!");

      router.push("/dashboard");

    } catch (error: any) {

        if (error.response?.status === 401) {

            toast.error("Invalid email or password.");

        } else if (error.code === "ERR_NETWORK") {

            toast.error("Cannot connect to the backend.");

        } else {

            toast.error("Something went wrong.");

        }

    } finally {

      setLoading(false);

    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--background)]">

      <Card className="w-full max-w-md">

        <SectionTitle
          title="Welcome Back"
          subtitle="Login to continue"
        />

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="space-y-5"
        >

          <div>

            <Input
              placeholder="Email"
              {...register("email")}
            />

            <p className="mt-1 text-sm text-red-400">
              {errors.email?.message}
            </p>

          </div>

          <div>

            <Input
              type="password"
              placeholder="Password"
              {...register("password")}
            />

            <p className="mt-1 text-sm text-red-400">
              {errors.password?.message}
            </p>

          </div>

          <Button
            loading={loading}
            type="submit"
          >
            Login
          </Button>

        </form>

        <div className="mt-6 text-center text-sm">

        Don't have an account?{" "}

            <Link
                href="/register"
                className="text-blue-500 hover:underline"
            >
                Register
            </Link>

        </div>

      </Card>

    </main>
  );
}