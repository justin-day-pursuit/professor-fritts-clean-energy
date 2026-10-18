/**
 * Where a claim came from: a clickable link for a web source, and the calculation id for math.
 * Used under every claim so a reader can always check the page or the calculation behind it.
 */
import type { Claim } from "@/lib/types";

export function ClaimSource({ claim }: { claim: Claim }) {
  const url = claim.source_url ?? "";
  const isWeb = url.startsWith("http://") || url.startsWith("https://");
  if (!isWeb && !claim.calc_id) return null;
  return (
    <span className="text-xs text-muted-foreground">
      {claim.calc_id && <>calculation {claim.calc_id}</>}
      {claim.calc_id && isWeb && " · "}
      {isWeb && (
        <a className="underline" href={url} target="_blank" rel="noreferrer">
          source
        </a>
      )}
    </span>
  );
}
