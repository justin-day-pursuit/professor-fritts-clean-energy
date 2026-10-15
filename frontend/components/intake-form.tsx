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
import { getRoofSuggestion } from "@/lib/api";
import { NYC_BOROUGHS, ROOF_TYPES, isNotFlat, missingRequiredFields } from "@/lib/profile-utils";
import type { IntakeProfile, RoofSuggestion } from "@/lib/types";
import { useState, type ReactNode } from "react";

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

  // The roof suggestion from city footprints. It fills the roof area box with a suggestion the user can
  // edit; it is never applied on its own, and the note under the box says it is not a measured roof.
  const [suggestion, setSuggestion] = useState<RoofSuggestion | null>(null);
  const [suggestionError, setSuggestionError] = useState<string | null>(null);
  const [suggesting, setSuggesting] = useState(false);

  async function suggestRoofArea() {
    setSuggesting(true);
    setSuggestionError(null);
    try {
      const result = await getRoofSuggestion(
        String(profile.address ?? ""),
        String(profile.borough ?? profile.county ?? ""),
      );
      setSuggestion(result);
      set("roof_area_sqft", String(result.suggested_roof_area_sqft));
    } catch (err) {
      setSuggestion(null);
      setSuggestionError(
        err instanceof Error && err.message
          ? `${err.message} Type the roof area instead.`
          : "Could not look up the roof. Type the roof area instead.",
      );
    } finally {
      setSuggesting(false);
    }
  }

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
          {/* NYC only: the borough is a pick-list of the five boroughs, so a typo or an upstate town cannot be sent. */}
          <Field id="borough" label="Borough" required>
            <Select
              value={NYC_BOROUGHS.find((b) => b === (profile.borough ?? profile.county)) ?? null}
              onValueChange={(v) => set("borough", v ?? "")}
            >
              <SelectTrigger id="borough" className="w-full">
                <SelectValue placeholder="Choose a borough" />
              </SelectTrigger>
              <SelectContent>
                {NYC_BOROUGHS.map((b) => (
                  <SelectItem key={b} value={b}>
                    {b}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          {/* The state is fixed to NY because the tool only covers New York City. */}
          <Field id="state" label="State">
            <Input id="state" value="NY" readOnly disabled />
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
          {/* A pick-list, because the planner treats a roof that is not flat differently (see the note below). */}
          <Field id="roof_type" label="Roof type">
            <Select
              value={ROOF_TYPES.find((r) => r.value === profile.roof_type)?.value ?? null}
              onValueChange={(v) => set("roof_type", v ?? "")}
            >
              <SelectTrigger id="roof_type" className="w-full">
                <SelectValue placeholder="Choose" />
              </SelectTrigger>
              <SelectContent>
                {ROOF_TYPES.map((r) => (
                  <SelectItem key={r.value} value={r.value}>
                    {r.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
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
        <div className="grid gap-1.5">
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={busy || suggesting || !profile.address || !(profile.borough || profile.county)}
            onClick={suggestRoofArea}
          >
            {suggesting ? "Looking up city records…" : "Not sure? Suggest roof area from city records"}
          </Button>
          {suggestionError && <p className="text-xs text-destructive">{suggestionError}</p>}
          {suggestion && (
            <p className="text-xs text-muted-foreground">
              Suggested {suggestion.suggested_roof_area_sqft.toLocaleString()} sq ft from{" "}
              {suggestion.building_count} building outline{suggestion.building_count === 1 ? "" : "s"} (
              {suggestion.buildings
                .filter((b) => b.counted)
                .map((b) => b.area_sqft.toLocaleString())
                .join(" + ")}{" "}
              sq ft) on this tax lot.{" "}
              <a className="underline" href={suggestion.source_url} target="_blank" rel="noreferrer">
                NYC building footprints
              </a>
              . {suggestion.note}
            </p>
          )}
          <p className="text-xs text-muted-foreground">
            Whatever the roof area, have an engineer or roofer verify it before any design or purchase.
          </p>
        </div>
        {isNotFlat(profile.roof_type) && (
          <div className="grid gap-1.5 rounded-md border border-amber-500/60 p-2">
            <p className="text-xs">
              Solar is not sized for a pitched, mixed or other roof from the flat-roof defaults. Have an
              engineer or roofer verify the usable roof area (size, pitch, direction, structure, shading), then enter
              it here and re-plan.
            </p>
            <Field id="verified_usable_roof_sqft" label="Usable roof area verified by an engineer or roofer (sq ft)">
              <Input
                id="verified_usable_roof_sqft"
                inputMode="numeric"
                value={profile.verified_usable_roof_sqft ?? ""}
                onChange={(e) => set("verified_usable_roof_sqft", e.target.value)}
              />
            </Field>
          </div>
        )}
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
        {/* Systems the building already has, so the plan builds on them and does not start from nothing. */}
        <div className="grid gap-2 border-t pt-3">
          <p className="text-sm font-medium">Existing renewable and efficiency systems</p>
          <p className="text-xs text-muted-foreground">
            Tell us what the building already has. Write &quot;none&quot; if there is nothing to list.
          </p>
          <div className="grid grid-cols-2 gap-2">
            <Field id="existing_solar_kw" label="Solar already on the roof (kW)">
              <Input
                id="existing_solar_kw"
                inputMode="decimal"
                value={profile.existing_solar_kw ?? ""}
                onChange={(e) => set("existing_solar_kw", e.target.value)}
              />
            </Field>
            <Field id="existing_solar_kwh" label="It makes (kWh per year)">
              <Input
                id="existing_solar_kwh"
                inputMode="numeric"
                value={profile.existing_solar_kwh ?? ""}
                onChange={(e) => set("existing_solar_kwh", e.target.value)}
              />
            </Field>
          </div>
          <Field id="existing_renewables" label="Other renewable sources (battery, geothermal, heat pumps…)">
            <Textarea
              id="existing_renewables"
              rows={2}
              value={profile.existing_renewables ?? ""}
              onChange={(e) => set("existing_renewables", e.target.value)}
            />
          </Field>
          <Field id="existing_efficiency" label="Energy efficiency work already done (LED, controls, HVAC, windows…)">
            <Textarea
              id="existing_efficiency"
              rows={2}
              value={profile.existing_efficiency ?? ""}
              onChange={(e) => set("existing_efficiency", e.target.value)}
            />
          </Field>
        </div>
      </CardContent>
    </Card>
  );
}
