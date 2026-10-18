/**
 * The address box on the first step of the form. As the visitor types, it offers matching New York City addresses in a
 * list to pick from. Picking one tells the page which building was chosen; typing again clears that choice.
 *
 * It waits a moment after each key press before asking the city, and drops an answer that arrives after the visitor has
 * typed more. It works with the keyboard (arrow keys, Enter, Escape) and announces itself to screen readers as a list box.
 */
"use client";

import { useEffect, useId, useRef, useState } from "react";
import { suggestAddresses, type AddressSuggestion } from "./address";

interface Props {
  /** Called when the visitor picks an address from the list. */
  onPick: (choice: AddressSuggestion) => void;
  /** Called when the visitor types after having picked, so the page can forget the earlier choice. */
  onEdit: () => void;
  /** Called when a search finishes, with the text searched and how many addresses came back (or -1 if the search failed). */
  onSearched: (text: string, count: number) => void;
  /** The address to show in the box when one was already chosen. */
  value: string;
}

const MIN_LETTERS = 3;
const WAIT_MS = 250;

export function AddressSearch({ onPick, onEdit, onSearched, value }: Props) {
  const [text, setText] = useState(value);
  const [results, setResults] = useState<{ q: string; items: AddressSuggestion[] } | null>(null);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const listId = useId();
  const searchedRef = useRef(onSearched);
  useEffect(() => {
    searchedRef.current = onSearched;
  });

  const query = text.trim();

  // Ask the city shortly after typing stops.
  useEffect(() => {
    if (query.length < MIN_LETTERS) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      suggestAddresses(query, controller.signal)
        .then((items) => {
          setResults({ q: query, items });
          setActive(-1);
          searchedRef.current(query, items.length);
        })
        .catch((error: unknown) => {
          if ((error as { name?: string }).name === "AbortError") return;
          setResults({ q: query, items: [] });
          searchedRef.current(query, -1);
        });
    }, WAIT_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  // Only answers for exactly what is typed now are shown.
  const items = results && results.q === query ? results.items : [];
  const searching = query.length >= MIN_LETTERS && !(results && results.q === query);
  const showList = open && items.length > 0;

  const choose = (item: AddressSuggestion) => {
    setText(item.label);
    setOpen(false);
    setActive(-1);
    onPick(item);
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown" && items.length) {
      e.preventDefault();
      setOpen(true);
      setActive((i) => (i + 1) % items.length);
    } else if (e.key === "ArrowUp" && items.length) {
      e.preventDefault();
      setActive((i) => (i <= 0 ? items.length - 1 : i - 1));
    } else if (e.key === "Enter" && showList && active >= 0) {
      e.preventDefault();
      choose(items[active]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  return (
    <div className="relative">
      <label htmlFor="address-search" className="block text-sm font-medium text-[var(--fr-ink)]">Building address</label>
      <input
        id="address-search"
        type="text"
        role="combobox"
        aria-expanded={showList}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={active >= 0 ? `${listId}-${active}` : undefined}
        autoComplete="off"
        placeholder="Start typing, for example 1871 Walton Avenue"
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setOpen(true);
          onEdit();
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onKeyDown={onKeyDown}
        className="mt-1 w-full rounded-lg border border-[var(--fr-line)] bg-white px-3 py-2 text-[var(--fr-ink)] outline-none focus:border-[var(--fr-teal)]"
      />
      <p className="mt-1 text-xs text-[var(--fr-mute)]">
        {searching ? "Looking in New York City…" : "New York City addresses only. Pick yours from the list."}
      </p>
      {showList && (
        <ul id={listId} role="listbox" className="absolute left-0 right-0 z-30 mt-1 max-h-72 overflow-auto rounded-xl border border-[var(--fr-line)] bg-white py-1 shadow-lg">
          {items.map((item, i) => (
            <li
              key={item.label}
              id={`${listId}-${i}`}
              role="option"
              aria-selected={i === active}
              onMouseDown={(e) => {
                e.preventDefault();
                choose(item);
              }}
              onMouseEnter={() => setActive(i)}
              className={`cursor-pointer px-3 py-2 text-sm text-[var(--fr-ink)] ${i === active ? "bg-[var(--fr-soft)]" : ""}`}
            >
              {item.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
