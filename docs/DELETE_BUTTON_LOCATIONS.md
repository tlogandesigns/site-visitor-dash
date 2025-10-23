# Delete Button Locations in UI

## Visual Guide: Where to Find Delete Buttons (Admin/Super Admin Only)

---

## Location 1: Visitors Table (Main Dashboard)

### Navigation Path:
1. Login as **admin** or **super_admin**
2. Click **"Dashboard"** tab (default view after login)
3. Look at the **"Visitors"** table below the stats cards

### Visual Layout:
```
┌─────────────────────────────────────────────────────────────────────┐
│  🏠 New Homes Lead Tracker                    👤 admin    [Logout]  │
├─────────────────────────────────────────────────────────────────────┤
│  [Dashboard] [Users]                                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  📊 Stats Cards (Total Visitors, Today, This Week, This Month)      │
│                                                                       │
│  ────────────────────────────────────────────────────────────────   │
│                                                                       │
│  Visitors                                          [+ Add Visitor]   │
│  Site: [All Sites ▼]  [🔄 Refresh] [📥 Export CSV]                  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Date      │ Name        │ Phone  │ Email │ ... │ Actions    │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │ 1/15/2025 │ John Smith  │ 555... │ j@... │ ... │ [👁️] [🗑️] │ ← Delete Button Here!
│  │ 1/14/2025 │ Jane Doe    │ 555... │ j@... │ ... │ [👁️] [🗑️] │   │
│  │ 1/13/2025 │ Bob Johnson │ 555... │ b@... │ ... │ [👁️] [🗑️] │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Button Details:
- **Icon:** 🗑️ (Red trash can icon)
- **Style:** Red outline button (`btn-outline-danger`)
- **Location:** Last column (Actions) of each visitor row
- **Next to:** Blue eye icon button (view details)
- **Only visible to:** admin and super_admin roles

### What It Does:
- Click the trash icon
- Confirmation modal appears
- Confirms deletion of that specific visitor
- Deletes visitor and all associated notes

---

## Location 2: Visitor Detail Modal

### Navigation Path:
1. Login as **admin** or **super_admin**
2. Go to **"Dashboard"** tab
3. Click **any visitor row** OR click the **blue eye icon** [👁️]
4. Modal window opens with visitor details

### Visual Layout:
```
┌────────────────────────────────────────────────────────────────┐
│  Visitor Details                                          [✖️]  │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Buyer Information              Visit Information              │
│  Name: John Smith               Site: Cedar Creek              │
│  Phone: 555-1234                Agent: Jane Realtor            │
│  Email: john@example.com        Date: 1/15/2025 10:30 AM      │
│  Timeline: 0-3 months           CINC: [Synced]                │
│  Price: $300k-$400k                                            │
│                                                                 │
│  ───────────────────────────────────────────────────────────── │
│                                                                 │
│  Notes History (3)                                             │
│  • Note 1 - Agent name - 1/15/2025 2:30 PM                    │
│  • Note 2 - Agent name - 1/14/2025 3:45 PM                    │
│  • Note 3 - Agent name - 1/13/2025 9:15 AM                    │
│                                                                 │
├────────────────────────────────────────────────────────────────┤
│  [🗑️ Delete Lead]  [Add note...              ] [+ Add Note]   │ ← Delete Button Here!
└────────────────────────────────────────────────────────────────┘
```

### Button Details:
- **Text:** "🗑️ Delete Lead"
- **Style:** Full red button (`btn-danger`)
- **Location:** Bottom left of modal footer
- **Only visible to:** admin and super_admin roles
- **Hidden for:** regular users (button won't show at all)

### What It Does:
- Click "Delete Lead" button
- Confirmation modal appears
- Confirms deletion
- Deletes visitor and all notes
- Closes the detail modal automatically

---

## Confirmation Modal (Appears for Both Locations)

### Visual Layout:
```
┌──────────────────────────────────────────────────┐
│  Confirm Lead Deletion                      [✖️] │
├──────────────────────────────────────────────────┤
│                                                   │
│  Are you sure you want to permanently delete     │
│  the lead for "John Smith"?                      │
│                                                   │
│  This action cannot be undone and will also      │
│  delete all associated notes.                    │
│                                                   │
├──────────────────────────────────────────────────┤
│                    [Cancel]  [Delete Lead]       │
└──────────────────────────────────────────────────┘
```

### Button Details:
- **Cancel:** Gray button - dismisses modal, no action
- **Delete Lead:** Red button - confirms deletion

---

## What Happens After Deletion

### Success:
```
┌─────────────────────────────────────────┐
│  ✅ Success                         [✖️] │
│  Lead "John Smith" deleted successfully │
└─────────────────────────────────────────┘
```
- Green toast notification appears (top-right corner)
- Visitor removed from table immediately
- Stats update automatically (total count decreases)
- Detail modal closes (if deletion from modal)

### Error (if not admin):
```
┌────────────────────────────────────────────────┐
│  ❌ Error                                  [✖️] │
│  Only administrators can delete visitors       │
└────────────────────────────────────────────────┘
```
- Red toast notification appears (top-right corner)
- No deletion occurs

---

## Who Can See Delete Buttons?

| Role | Table Delete Button | Modal Delete Button |
|------|-------------------|-------------------|
| **super_admin** | ✅ Visible | ✅ Visible |
| **admin** | ✅ Visible | ✅ Visible |
| **user** | ❌ Hidden | ❌ Hidden |
| **Not logged in** | ❌ N/A | ❌ N/A |

---

## Testing the Feature

### As Admin/Super Admin:
1. Login with admin credentials
2. Navigate to Dashboard
3. You should see **red trash icons** in the Actions column
4. Click any visitor row to open details
5. You should see **"Delete Lead"** button in bottom-left of modal

### As Regular User:
1. Login with user credentials
2. Navigate to Dashboard
3. You should **NOT** see any trash icons
4. Click any visitor row to open details
5. You should **NOT** see "Delete Lead" button

---

## Quick Reference

**Where to look:**
- 📍 **Location 1:** Dashboard tab → Visitors table → Actions column → 🗑️ icon
- 📍 **Location 2:** Dashboard tab → Click any visitor → Modal footer → "Delete Lead" button

**Who can see it:**
- ✅ Admin
- ✅ Super Admin
- ❌ Regular User

**What it deletes:**
- The visitor/lead record
- All associated notes (cascade)

**Confirmation:**
- ⚠️ Always requires confirmation
- Cannot be undone

---

## Screenshots Locations

If you need to capture screenshots:

1. **Main table view:** Dashboard → scroll to Visitors table
2. **Actions column:** Look at the rightmost column
3. **Delete button:** Red trash icon next to blue eye icon
4. **Detail modal:** Click any visitor to open modal
5. **Modal delete button:** Bottom-left red button

---

**Last Updated:** January 2025
