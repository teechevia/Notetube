# Responsive Layout Audit

## Root Causes Identified
1. **Three-Panel Flex Structure**: The `Workspace.jsx` uses a single `flex-row` (or `flex-col` on mobile) container for all three panels. On mobile, they are forced to stack vertically, which leads to nested scrollbars and a bizarrely tall single page.
2. **Lack of Drawer Architecture on Mobile**: Instead of acting as modal drawers or separate views, the sidebars just stack on top or below the chat on mobile, breaking the primary UX where Chat should be central.
3. **Absolute Positioning Conflicts**: The chat input and floating toasts in the center panel use absolute positioning relative to the container. When stacked on mobile, these bounds clash, causing overlap (as seen in the screenshots where the chat input floats weirdly).
4. **Header Wrapping**: "My Notebooks" on the dashboard uses standard flex without text truncating or proper alignment, causing ugly line breaks when squished.
5. **Fixed Dimensions**: Left and Right sidebars use fixed/min widths (`w-[300px]`, `w-[340px]`) which causes horizontal squishing on smaller desktops (like 1280px).

## Planned Architecture Changes
1. **Mobile (Single Column)**: Chat is the default view (`flex-1`). Sources and Studio become fixed/absolute full-screen slide-over drawers on screens `< 1024px` (lg).
2. **Tablet (lg - xl)**: Sources acts as a drawer, Chat + Studio share the screen.
3. **Desktop (xl+)**: True 3-column layout.
4. **Chat Composer**: Move it into the flex flow instead of absolute positioning to prevent overlap.
