"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { toast } from "sonner";

import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Input from "@/components/ui/Input";
import SectionTitle from "@/components/ui/SectionTitle";

import { register as registerUser } from "@/services/auth.service";
import Link from "next/link";

import {
  registerSchema,
  RegisterFormData,
} from "@/lib/validation";

export default function RegisterPage() {

  const router = useRouter();

  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  async function onSubmit(data: RegisterFormData) {

    try {

      setLoading(true);

      await registerUser(data);

      toast.success("Account created successfully.");

      router.push("/login");

    } catch (error: any) {

      if (error.response?.status === 409) {

        toast.error("Email already exists.");

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
          title="Create Account"
          subtitle="Start your AI Interview journey"
        />

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="space-y-5"
        >

          <div>

            <Input
              placeholder="Full Name"
              {...register("name")}
            />

            <p className="text-sm text-red-400">
              {errors.name?.message}
            </p>

          </div>

          <div>

            <Input
              placeholder="Email"
              {...register("email")}
            />

            <p className="text-sm text-red-400">
              {errors.email?.message}
            </p>

          </div>

          <div>

            <Input
              type="password"
              placeholder="Password"
              {...register("password")}
            />

            <p className="text-sm text-red-400">
              {errors.password?.message}
            </p>

          </div>

          <Button
            loading={loading}
            type="submit"
          >
            Register
          </Button>

        </form>

        <div className="mt-6 text-center text-sm">

            Already have an account?{" "}

            <Link
                href="/login"
                className="text-blue-500 hover:underline"
            >
                Login
            </Link>

        </div>

      </Card>

    </main>

  );

}