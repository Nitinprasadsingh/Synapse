"use client";

import React, { useState } from "react";
import Link from "next/navigation";
import { usePathname } from "next/navigation";
import NextLink from "next/link";
import {
  LayoutDashboard,
  Sun,
  BatteryCharging,
  Zap,
  BarChart3,
  Bell,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  Cpu
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth/AuthContext";

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  roles?: string[];
}

const navItems: NavItem[] = [
  { name: "Overview", href: "/dashboard/overview", icon: LayoutDashboard },
  { name: "Forecasting", href: "/dashboard/forecasting", icon: Sun },
  { name: "Battery Scheduling", href: "/dashboard/battery", icon: BatteryCharging },
  { name: "Grid Optimization", href: "/dashboard/grid", icon: Zap },
  { name: "Analytics & Reports", href: "/dashboard/analytics", icon: BarChart3 },
  { name: "Alerts", href: "/dashboard/alerts", icon: Bell },
  { name: "System Settings", href: "/dashboard/settings", icon: Settings },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();
  const { user } = useAuth();

  return (
    <aside
      className={cn(
        "flex flex-col bg-slate-900 text-slate-200 border-r border-slate-800 transition-all duration-300 z-30 select-none",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Brand Header */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-slate-800">
        <NextLink href="/dashboard/overview" className="flex items-center gap-3 overflow-hidden">
          <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex-shrink-0">
            <Cpu className="w-5 h-5 text-emerald-400" />
          </div>
          {!collapsed && (
            <div className="flex flex-col truncate">
              <span className="font-bold text-sm tracking-wide text-white uppercase">MicroGrid AI</span>
              <span className="text-[10px] text-slate-400 truncate">Load Balancing & Solar PV</span>
            </div>
          )}
        </NextLink>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation items */}
      <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <NextLink
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors group",
                isActive
                  ? "bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-sm"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/60"
              )}
              title={collapsed ? item.name : undefined}
            >
              <Icon
                className={cn(
                  "w-5 h-5 flex-shrink-0 transition-colors",
                  isActive ? "text-blue-400" : "text-slate-400 group-hover:text-white"
                )}
              />
              {!collapsed && <span className="truncate">{item.name}</span>}
            </NextLink>
          );
        })}
      </nav>

      {/* Microgrid State Indicator in Footer */}
      {!collapsed && (
        <div className="p-4 m-3 rounded-lg bg-slate-800/60 border border-slate-700/60 text-xs">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-slate-400 font-medium">SCADA Controller</span>
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
          </div>
          <div className="text-[11px] text-slate-300">
            Dispatch: <span className="text-emerald-400 font-mono font-semibold">Active</span>
          </div>
          <div className="text-[11px] text-slate-400">
            Freq: <span className="font-mono text-slate-300">50.02 Hz</span>
          </div>
        </div>
      )}
    </aside>
  );
}
