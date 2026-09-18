/**
 * Single source of truth for which visual theme the app renders.
 *
 * Only "gradient" has CSS defined right now (see the [data-theme="gradient"]
 * block in globals.css) — every color/radius/shadow a component uses comes
 * from that block's CSS custom properties, never a hardcoded value. To add
 * another theme later:
 *   1. Add a `[data-theme="<name>"] { --bg: ...; ... }` block to globals.css
 *      defining the same variable names with new values.
 *   2. Add "<name>" to the ThemeName union below.
 *   3. Set ACTIVE_THEME to it.
 * That's the whole change — no component touches a color/radius directly.
 */
export type ThemeName = "gradient";

export const ACTIVE_THEME: ThemeName = "gradient";
