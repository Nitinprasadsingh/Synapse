"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/AuthContext";
import { Cpu, ShieldCheck, Lock, AlertCircle, KeyRound, Sparkles } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.push("/dashboard/overview");
    } catch (err: any) {
      setError(err.message || "Invalid authentication credentials");
    } finally {
      setLoading(false);
    }
  };

  const fillCredentials = (role: "admin" | "operator" | "analyst") => {
    if (role === "admin") {
      setEmail("admin@microgrid.io");
      setPassword("Admin@12345");
    } else if (role === "operator") {
      setEmail("operator@microgrid.io");
      setPassword("Operator@12345");
    } else {
      setEmail("analyst@microgrid.io");
      setPassword("Analyst@12345");
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 flex-col justify-center items-center p-4">
      {/* Background Graphic Grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:32px_32px] opacity-25 pointer-events-none" />

      <div className="relative z-10 w-full max-w-md">
        {/* SCADA Logo & Header */}
        <div className="flex flex-col items-center text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-4 shadow-lg shadow-emerald-500/10">
            <Cpu className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-black tracking-tight text-white uppercase">
            MicroGrid AI
          </h1>
          <p className="text-xs font-mono text-slate-400 mt-1 max-w-xs">
            Intelligent Load Balancing & Operational Solar Energy Forecasting
          </p>
        </div>

        {/* Login Card */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-8 shadow-2xl backdrop-blur-sm">
          <div className="flex items-center justify-between pb-4 mb-6 border-b border-slate-800">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              System Access Authentication
            </span>
            <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              <ShieldCheck className="w-3 h-3" />
              JWT Authenticated
            </span>
          </div>

          {error && (
            <div className="mb-5 p-3 rounded-lg bg-red-500/15 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-1.5">
                Operator / User Email
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@microgrid.io"
                className="w-full h-10 px-3 rounded-lg bg-slate-950 border border-slate-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono placeholder:text-slate-600"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-1.5">
                Access Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full h-10 px-3 rounded-lg bg-slate-950 border border-slate-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono placeholder:text-slate-600"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full h-10 mt-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm transition-all shadow-md shadow-emerald-900/40 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <KeyRound className="w-4 h-4" />
                  <span>Authenticate Session</span>
                </>
              )}
            </button>
          </form>

          {/* Quick role credential selector */}
          <div className="mt-6 pt-5 border-t border-slate-800">
            <div className="flex items-center justify-between mb-2.5">
              <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-amber-400" />
                Select Seed Role Credentials:
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => fillCredentials("admin")}
                className="py-1.5 px-2 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors text-center"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => fillCredentials("operator")}
                className="py-1.5 px-2 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors text-center"
              >
                Operator
              </button>
              <button
                type="button"
                onClick={() => fillCredentials("analyst")}
                className="py-1.5 px-2 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors text-center"
              >
                Analyst
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-6 text-[11px] text-slate-500 font-mono">
          B.Tech Minor Project • CSE-AIML 
        </div>
      </div>
    </div>
  );
}
