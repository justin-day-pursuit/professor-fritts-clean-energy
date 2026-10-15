/**
 * Left column intake form — building details, budget, goals, and critical loads.
 * Parent owns session id; this component only edits local profile state and calls save/load hooks.
 */
"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { missingRequiredFields } from "@/lib/profile-utils";
import type { IntakeProfile } from "@/lib/types";
import type { ReactNode } from "react";

export interface IntakeFormProps {
  profile: IntakeProfile;
  onChange: (next: IntakeProfile) => void;
  onLoadDana: () => void;
  onUpdateAndReplan: () => void;
  busy: boolean;
}

function Field({
  id,
  label,
  required,
  children,
}: {
  id: string;
  label: string;
  required?: boolean;
  children: ReactNode;
}) {
  return (
    <div className="grid gap-1.5">
      <Label htmlFor={id}>
        {label}
        {required && <span aria-hidden="true"> *</span>}
      </Label>
      {children}
    </div>
  );
}

export function IntakeForm({
  profile,
  onChange,
  onLoadDana,
  onUpdateAndReplan,
  busy,
}: IntakeFormProps) {
  const set = (key: keyof IntakeProfile, value: string) => {
    onChange({ ...profile, [key]: value });
  };
  const missing = missingRequiredFields(profile);

  return (
    <Card className="h-full flex flex-col min-h-0">
      <CardHeader className="pb-3 shrink-0">
        <CardTitle className="text-base">Intake</CardTitle>
        <div className="flex flex-wrap gap-2 pt-1">
          <Button type="button" size="sm" variant="secondary" disabled={busy} onClick={onLoadDana}>
            Load Dana&apos;s example
          </Button>
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={busy || missing.length > 0}
            onClick={onUpdateAndReplan}
          >
            Update intake and re-plan
          </Button>
        </div>
        {missing.length > 0 && (
          <p className="pt-1 text-xs text-muted-foreground">Still needed: {missing.join(", ")}</p>
        )}
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto space-y-3 text-sm pb-4">
        <Field id="address" label="Address" required>
          <Input
            id="address"
            value={profile.address ?? ""}
            onChange={(e) => set("address", e.target.value)}
          />
        </Field>
        <div className="grid grid-cols-2 gap-2">
          <Field id="borough" label="Borough or county" required>
            <Input
              id="borough"
              value={profile.borough ?? profile.county ?? ""}
              onChange={(e) => set("borough", e.target.value)}
            />
          </Field>
          <Field id="state" label="State">
            <Input id="state" value={profile.state ?? ""} onChange={(e) => set("state", e.target.value)} />
          </Field>
        </div>
        <Field id="building_type" label="Building type">
          <Input
            id="building_type"
            value={profile.building_type ?? ""}
            onChange={(e) => set("building_type", e.target.value)}
          />
        </Field>
        <div className="grid grid-cols-2 gap-2">
          <Field id="floor_area_sqft" label="Floor area (sq ft)">
            <Input
              id="floor_area_sqft"
              inputMode="numeric"
              value={profile.floor_area_sqft ?? ""}
              onChange={(e) => set("floor_area_sqft", e.target.value)}
            />
          </Field>
          <Field id="year_built" label="Year built">
            <Input
              id="year_built"
              inputMode="numeric"
              value={profile.year_built ?? ""}
              onChange={(e) => set("year_built", e.target.value)}
            />
          </Field>
        </div>
        <div className="grid grid-cols-3 gap-2">
          <Field id="roof_type" label="Roof type">
            <Input
              id="roof_type"
              value={profile.roof_type ?? ""}
              onChange={(e) => set("roof_type", e.target.value)}
            />
          </Field>
          <Field id="roof_area_sqft" label="Roof area (sq ft)" required>
            <Input
              id="roof_area_sqft"
              inputMode="numeric"
              value={profile.roof_area_sqft ?? ""}
              onChange={(e) => set("roof_area_sqft", e.target.value)}
            />
          </Field>
          <Field id="roof_replaced_year" label="Roof replaced (year)">
            <Input
              id="roof_replaced_year"
              inputMode="numeric"
              value={profile.roof_replaced_year ?? ""}
              onChange={(e) => set("roof_replaced_year", e.target.value)}
            />
          </Field>
        </div>
        <Field id="utility" label="Utility">
          <Input
            id="utility"
            value={profile.utility ?? ""}
            onChange={(e) => set("utility", e.target.value)}
          />
        </Field>
        <Field id="annual_kwh" label="Annual kWh (or upload bills below)">
          <Input
            id="annual_kwh"
            inputMode="numeric"
            value={profile.annual_kwh ?? ""}
            onChange={(e) => set("annual_kwh", e.target.value)}
          />
        </Field>
        <div className="grid grid-cols-3 gap-2">
          <Field id="budget_amount" label="Budget amount">
            <Input
              id="budget_amount"
              inputMode="numeric"
              value={profile.budget_amount ?? ""}
              onChange={(e) => set("budget_amount", e.target.value)}
            />
          </Field>
          <Field id="budget_year" label="Budget year">
            <Input
              id="budget_year"
              inputMode="numeric"
              value={profile.budget_year ?? ""}
              onChange={(e) => set("budget_year", e.target.value)}
            />
          </Field>
          <Field id="budget_type" label="Capital or annual">
            <Select
              value={profile.budget_type ?? "capital"}
              onValueChange={(v) => set("budget_type", v ?? "capital")}
            >
              <SelectTrigger id="budget_type" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="capital">Capital</SelectItem>
                <SelectItem value="annual">Annual</SelectItem>
              </SelectContent>
            </Select>
          </Field>
        </div>
        <Field id="goal" label="Energy goal">
          <Textarea
            id="goal"
            rows={2}
            value={profile.goal ?? ""}
            onChange={(e) => set("goal", e.target.value)}
          />
        </Field>
        <Field id="target_year" label="Target year">
          <Input
            id="target_year"
            inputMode="numeric"
            value={profile.target_year ?? ""}
            onChange={(e) => set("target_year", e.target.value)}
          />
        </Field>
        <Field id="critical_loads" label="Critical loads">
          <Textarea
            id="critical_loads"
            rows={2}
            value={profile.critical_loads ?? ""}
            onChange={(e) => set("critical_loads", e.target.value)}
          />
        </Field>
        <Field id="critical_load_hours" label="Critical load hours">
          <Input
            id="critical_load_hours"
            inputMode="numeric"
            value={profile.critical_load_hours ?? ""}
            onChange={(e) => set("critical_load_hours", e.target.value)}
          />
        </Field>
      </CardContent>
    </Card>
  );
}
