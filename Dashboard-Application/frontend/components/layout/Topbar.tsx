"use client";

import React, { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import NextLink from "next/link";
import {
  Bell,
  LogOut,
  User as UserIcon,
  Clock,
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  RefreshCw
} from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import { endpoints } from "@/lib/api/endpoints";

export function Topbar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [currentTime, setCurrentTime] = useState<string>("");
  const [unreadAlerts, setUnreadAlerts] = useState<number>(0);
  const [systemStatus, setSystemStatus] = useState<"Normal" | "Warning" | "Critical">("Normal");

  // Format page title
  const pageTitles: Record<string, string> = {
    "/dashboard/overview": "Operational Overview & SCADA",
    "/dashboard/forecasting": "Solar PV & Load Demand Forecasting",
    "/dashboard/battery": "Battery Storage Dispatch & Scheduling",
    "/dashboard/grid": "Grid Interconnection & Tariff Optimization",
    "/dashboard/analytics": "Energy Analytics & Historical Reports",
    "/dashboard/alerts": "System Event Alerts & Alarms",
    "/dashboard/settings": "System Parameters & Operational Configuration",
  };
  const title = pageTitles[pathname] || "Microgrid Management";

  // Clock
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleString("en-US", {
          month: "short",
          day: "numeric",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
        })
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Poll alerts count & status
  useEffect(() => {
    const fetchAlertsAndStatus = async () => {
      try {
        const alerts = await endpoints.getAlerts({ is_acknowledged: false });
        setUnreadAlerts(alerts.length);

        const overview = await endpoints.getDashboardOverview();
        if (overview.operational_status) {
          setSystemStatus(overview.operational_status);
        }
      } catch {
        // Silently catch in topbar poll
      }
    };
    fetchAlertsAndStatus();
    const interval = setInterval(fetchAlertsAndStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="flex items-center justify-between h-16 px-6 bg-white border-b border-slate-200 shadow-sm z-20">
      {/* Page Title & Status */}
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-bold text-slate-800 tracking-tight">{title}</h1>

        {/* System Status Pill */}
        <div
          className={`hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
            systemStatus === "Normal"
              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
              : systemStatus === "Warning"
              ? "bg-amber-50 text-amber-700 border border-amber-200"
              : "bg-red-50 text-red-700 border border-red-200"
          }`}
        >
          {systemStatus === "Normal" && <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />}
          {systemStatus === "Warning" && <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />}
          {systemStatus === "Critical" && <AlertOctagon className="w-3.5 h-3.5 text-red-600" />}
          <span>Status: {systemStatus}</span>
        </div>

      </div>

      {/* Right Action Bar */}
      <div className="flex items-center gap-4">
        {/* Current Date/Time */}
        <div className="hidden lg:flex items-center gap-1.5 text-xs text-slate-500 font-mono bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-md">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>{currentTime || "Loading time..."}</span>
        </div>

        {/* Notifications Alert Bell */}
        <NextLink
          href="/dashboard/alerts"
          className="relative p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-md transition-colors"
          title="Active Alerts"
        >
          <Bell className="w-5 h-5" />
          {unreadAlerts > 0 && (
            <span className="absolute top-1 right-1 flex items-center justify-center w-4 h-4 text-[10px] font-bold text-white bg-red-600 rounded-full animate-pulse">
              {unreadAlerts}
            </span>
          )}
        </NextLink>

        {/* User Profile Menu */}
        <div className="flex items-center gap-3 pl-3 border-l border-slate-200">
          <div className="flex flex-col text-right">
            <span className="text-xs font-semibold text-slate-800 leading-tight">
              {user?.full_name || user?.email || "Operator"}
            </span>
            <span className="text-[10px] font-mono uppercase text-blue-600 font-bold tracking-wider">
              {user?.role || "Operator"}
            </span>
          </div>

          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-slate-100 border border-slate-300 text-slate-700">
            <UserIcon className="w-4 h-4" />
          </div>

          <button
            onClick={logout}
            className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
            title="Sign Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
