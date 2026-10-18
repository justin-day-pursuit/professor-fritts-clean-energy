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
import {
  COOLING_TYPES,
  DEFAULT_GOAL_PERCENT,
  GOAL_PRESETS,
  GOAL_TYPES,
  HEATING_FUELS,
  LIGHTING_TYPES,
  NYC_BOROUGHS,
  OWNER_AGENCIES,
  ROOF_CONDITIONS,
  ROOF_TYPES,
  YES_NO,
  isNotFlat,
  missingRequiredFields,
} from "@/lib/profile-utils";
import type { IntakeProfile, ReplayCase, RoofSuggestion } from "@/lib/types";
import { useState, type ReactNode } from "react";

export interface IntakeFormProps {
  profile: IntakeProfile;
  onChange: (next: IntakeProfile) => void;
  onLoadDana: () => void;
  onUpdateAndReplan: () => void;
  busy: boolean;
  /** Saved demos for the replay menu; leave empty to hide it. Replays never call Claude. */
  replayCases?: ReplayCase[];
  onReplay?: (caseId: string) => void;
  /** True while a replay is on screen: re-planning is switched off so no new (paid) run can start from here. */
  replayLocked?: boolean;
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

/**
 * A labeled pick-list for the optional questions. Each option list ends with "Don't know", so nobody has to
 * guess; the plan treats that the same as a blank answer.
 */
function PickField({
  id,
  label,
  value,
  options,
  placeholder = "Choose one",
  onPick,
}: {
  id: string;
  label: string;
  value: string | undefined;
  options: readonly { value: string; label: string }[];
  placeholder?: string;
  onPick: (value: string) => void;
}) {
  return (
    <Field id={id} label={label}>
      <Select
        value={options.find((o) => o.value === value)?.value ?? null}
        onValueChange={(v) => onPick(v ?? "")}
      >
        <SelectTrigger id={id} className="w-full">
          <SelectValue placeholder={placeholder}>
            {(v: string | null) => options.find((o) => o.value === v)?.label ?? placeholder}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {options.map((o) => (
            <SelectItem key={o.value} value={o.value}>
              {o.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </Field>
  );
}

export function IntakeForm({
  profile,
  onChange,
  onLoadDana,
  onUpdateAndReplan,
  busy,
  replayCases = [],
  onReplay,
  replayLocked = false,
}: IntakeFormProps) {
  const set = (key: keyof IntakeProfile, value: string) => {
    onChange({ ...profile, [key]: value });
  };
  const missing = missingRequiredFields(profile);
  // The goal slider: a blank or unusable number shows the default position, and the hint turns the percent into kWh.
  const typedGoal = Number(profile.goal_percent);
  const goalPercent =
    Number.isFinite(typedGoal) && typedGoal >= 5 && typedGoal <= 100 ? typedGoal : DEFAULT_GOAL_PERCENT;
  const annualKwh = Number(String(profile.annual_kwh ?? "").replace(/,/g, ""));
  const goalHint =
    Number.isFinite(annualKwh) && annualKwh > 0
      ? `${goalPercent}% of your ${Math.round(annualKwh).toLocaleString()} kWh a year is about ${Math.round(
          (annualKwh * goalPercent) / 100,
        ).toLocaleString()} kWh a year.`
      : "Enter annual kWh (or upload bills) to see what this means in kWh.";
  // The saved demo picked in the replay menu. Pressing Replay sends it to the page, which plays it back.
  const [replayChoice, setReplayChoice] = useState<string | null>(null);
  const chosenReplay = replayCases.find((c) => c.id === replayChoice) ?? null;

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
            disabled={busy || missing.length > 0 || replayLocked}
            onClick={onUpdateAndReplan}
          >
            Update intake and re-plan
          </Button>
        </div>
        {/* Replay menu: plays a saved run back with no Claude call, so it costs nothing. */}
        {replayCases.length > 0 && onReplay && (
          <div className="grid gap-1 pt-1">
            <div className="flex flex-wrap items-center gap-2">
              <Select value={replayChoice} onValueChange={(v) => setReplayChoice(v ?? null)}>
                <SelectTrigger className="h-8 w-64 text-xs" aria-label="Choose a saved demo to replay">
                  <SelectValue placeholder="Replay a saved demo…" />
                </SelectTrigger>
                <SelectContent>
                  {replayCases.map((c) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.label} ({c.kind === "recorded" ? "recording" : "script"})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                type="button"
                size="sm"
                disabled={busy || !chosenReplay}
                onClick={() => chosenReplay && onReplay(chosenReplay.id)}
              >
                Replay
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              {chosenReplay
                ? chosenReplay.tag
                : "Plays a saved run back step by step. No Claude call, no cost."}
            </p>
          </div>
        )}
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
        <p className="-mt-2 text-xs text-muted-foreground">
          kWh is the electricity you buy over a year. It&apos;s on your Con Edison bills, and the city&apos;s energy
          report may already list it for your building.
        </p>
        <Field id="electricity_rate_usd_per_kwh" label="Your electricity price ($ per kWh, optional)">
          <Input
            id="electricity_rate_usd_per_kwh"
            inputMode="decimal"
            placeholder="for example 0.26"
            value={profile.electricity_rate_usd_per_kwh ?? ""}
            onChange={(e) => set("electricity_rate_usd_per_kwh", e.target.value)}
          />
        </Field>
        <p className="-mt-2 text-xs text-muted-foreground">
          From a bill: total charges divided by the kWh used. Leave it blank and the plan uses the New York average and
          says so.
        </p>
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
        {/* The goal: a percent cut in grid electricity. The model uses this number directly. */}
        <div className="grid gap-2 border-t pt-3">
          <p className="text-sm font-medium">Your goal</p>
          <PickField
            id="goal_type"
            label="What is the goal?"
            value={profile.goal_type ?? "percent_reduction"}
            options={GOAL_TYPES}
            onPick={(v) => set("goal_type", v)}
          />
          {(profile.goal_type ?? "percent_reduction") !== "percent_reduction" && (
            <p className="text-xs text-muted-foreground">
              Only a percent cut in grid electricity is calculated. Other goals are noted in the plan but not
              modeled.
            </p>
          )}
          <Field id="goal_percent" label={`Cut grid electricity by ${goalPercent}%`}>
            <div className="grid gap-2">
              <div className="flex items-center gap-2">
                <input
                  id="goal_percent"
                  type="range"
                  min={5}
                  max={100}
                  step={5}
                  value={goalPercent}
                  onChange={(e) => onChange({ ...profile, goal_percent: Number(e.target.value) })}
                  className="flex-1"
                  aria-label="Goal percent"
                />
                <Input
                  aria-label="Goal percent number"
                  className="w-20"
                  inputMode="numeric"
                  value={profile.goal_percent ?? ""}
                  onChange={(e) => set("goal_percent", e.target.value)}
                />
              </div>
              <div className="flex gap-1">
                {GOAL_PRESETS.map((n) => (
                  <Button
                    key={n}
                    type="button"
                    size="sm"
                    variant={goalPercent === n ? "default" : "outline"}
                    onClick={() => onChange({ ...profile, goal_percent: n })}
                  >
                    {n}%
                  </Button>
                ))}
              </div>
              {goalHint && <p className="text-xs text-muted-foreground">{goalHint}</p>}
            </div>
          </Field>
          <Field id="target_year" label="Target year">
            <Input
              id="target_year"
              inputMode="numeric"
              value={profile.target_year ?? ""}
              onChange={(e) => set("target_year", e.target.value)}
            />
          </Field>
          <Field id="goal" label="Anything else about the goal (optional)">
            <Textarea
              id="goal"
              rows={2}
              value={profile.goal ?? ""}
              onChange={(e) => set("goal", e.target.value)}
            />
          </Field>
        </div>
        {/* Backup power: the battery is sized from these two numbers. Blank ones are estimated and labeled in the plan. */}
        <div className="grid gap-2 border-t pt-3">
          <p className="text-sm font-medium">Backup power</p>
          <Field id="critical_loads" label="Critical loads">
            <Textarea
              id="critical_loads"
              rows={2}
              value={profile.critical_loads ?? ""}
              onChange={(e) => set("critical_loads", e.target.value)}
            />
          </Field>
          <div className="grid grid-cols-2 gap-2">
            <Field id="critical_load_kw" label="Critical load (kW)">
              <Input
                id="critical_load_kw"
                inputMode="decimal"
                value={profile.critical_load_kw ?? ""}
                onChange={(e) => set("critical_load_kw", e.target.value)}
              />
            </Field>
            <Field id="backup_hours_wanted" label="Hours of backup wanted">
              <Input
                id="backup_hours_wanted"
                inputMode="numeric"
                value={profile.backup_hours_wanted ?? ""}
                onChange={(e) => set("backup_hours_wanted", e.target.value)}
              />
            </Field>
          </div>
          <p className="text-xs text-muted-foreground">
            Critical load is how much power the things that must keep running draw at one moment (emergency lighting,
            communications, boiler controls). Backup hours is how long they need to run. If you don&apos;t know, leave
            these blank: the plan estimates them and says so.
          </p>
        </div>
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
        {/* Optional questions that sharpen the plan. Skipping any is fine: "Don't know" counts as blank. */}
        <div className="grid gap-2 border-t pt-3">
          <p className="text-sm font-medium">More about the building (optional)</p>
          <PickField
            id="owner_agency"
            label="Who owns the building?"
            value={profile.owner_agency}
            options={OWNER_AGENCIES}
            onPick={(v) => set("owner_agency", v)}
          />
          <PickField
            id="roof_condition"
            label="Roof condition"
            value={profile.roof_condition}
            options={ROOF_CONDITIONS}
            onPick={(v) => set("roof_condition", v)}
          />
          <div className="grid grid-cols-2 gap-2">
            <PickField
              id="lighting_type"
              label="Lighting"
              value={profile.lighting_type}
              options={LIGHTING_TYPES}
              onPick={(v) => set("lighting_type", v)}
            />
            <Field id="lighting_retrofit_year" label="Lighting last upgraded (year)">
              <Input
                id="lighting_retrofit_year"
                inputMode="numeric"
                value={profile.lighting_retrofit_year ?? ""}
                onChange={(e) => set("lighting_retrofit_year", e.target.value)}
              />
            </Field>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <PickField
              id="heating_fuel"
              label="Heating fuel"
              value={profile.heating_fuel}
              options={HEATING_FUELS}
              onPick={(v) => set("heating_fuel", v)}
            />
            <PickField
              id="cooling_type"
              label="Cooling"
              value={profile.cooling_type}
              options={COOLING_TYPES}
              onPick={(v) => set("cooling_type", v)}
            />
          </div>
          <PickField
            id="has_building_controls"
            label="Building automation or controls?"
            value={profile.has_building_controls}
            options={YES_NO}
            onPick={(v) => set("has_building_controls", v)}
          />
        </div>
      </CardContent>
    </Card>
  );
}
