# Implementation Plan: Camera-View Projection for Hit Detection

## Overview
Change collision detection from fixed XZ plane (bird's eye view) to camera-view projection (screen space). This will make hit detection match what the player sees on screen.

## Current Implementation Analysis

### Current Method (XZ Plane Projection)
- **Backend** (`drum_collision.py:356-368`): Calculates 2D distance ignoring Y axis
  ```python
  dx = tip_x - drum_x
  dz = tip_z - drum_z
  distance_2d = math.sqrt(dx * dx + dz * dz)
  ```
- **Frontend** (`drum_3d.js:376-436`): Same XZ plane logic
  ```javascript
  const dx = tipX - drumX;
  const dz = tipZ - drumZ;
  const distanceXZ = Math.sqrt(dx * dx + dz * dz);
  ```

### Camera Configuration
- Position: `[0, 3.5, -4]` (behind and above drum set)
- Look at: `[0, 0, 2]` (slightly forward)
- FOV: 60°, Aspect: 1.5

## Proposed Solution

### Architecture Decision
**Use frontend-only camera projection with backend validation**

Rationale:
1. Camera projection requires Three.js perspective camera object (not available in backend)
2. Backend doesn't need to know about screen-space coordinates
3. Frontend already has access to all 3D positions and camera
4. Backend can validate hit detection using simplified world-space logic

### Implementation Approach

#### Phase 1: Frontend Camera-View Projection (Primary Change)

**File**: `static/js/drum_3d.js`

**Modify `solveStickCollision()` function (lines 376-436)**:

1. **Project 3D positions to 2D screen space**:
   ```javascript
   // Create vectors for projection
   const tipVector = new THREE.Vector3(tipX, tipY, tipZ);
   const drumVector = new THREE.Vector3(drumX, drumY, drumZ);

   // Project to normalized device coordinates (-1 to +1)
   const tipScreen = tipVector.clone().project(camera);
   const drumScreen = drumVector.clone().project(camera);
   ```

2. **Calculate 2D screen-space distance**:
   ```javascript
   // Calculate distance in screen space (normalized coordinates)
   const dx = tipScreen.x - drumScreen.x;
   const dy = tipScreen.y - drumScreen.y;
   const screenDistance = Math.sqrt(dx * dx + dy * dy);
   ```

3. **Convert drum radius to screen space**:
   ```javascript
   // Project drum edge to get screen-space radius
   const drumEdgeWorld = new THREE.Vector3(
     drumX + drum.radius,
     drumY,
     drumZ
   );
   const drumEdgeScreen = drumEdgeWorld.clone().project(camera);
   const screenRadius = Math.abs(drumEdgeScreen.x - drumScreen.x);
   ```

4. **Collision detection**:
   ```javascript
   if (screenDistance <= screenRadius + HIT_RADIUS_OFFSET) {
     // Hit detected in screen space
     return drum.name;
   }
   ```

**Add configuration to `3d_settings.js`**:
```javascript
// Screen-space collision settings
const SCREEN_HIT_RADIUS_OFFSET = 0.05;  // Additional hit tolerance in screen space
const USE_CAMERA_PROJECTION = true;  // Toggle between XZ and camera projection
```

#### Phase 2: Backend Validation (Secondary)

**File**: `drum_collision.py`

**Keep existing XZ plane logic as fallback**, but add a looser tolerance:

```python
# Existing logic with relaxed threshold for camera-projection mode
CAMERA_PROJECTION_MODE = True
distance_threshold = radius * 1.5 if CAMERA_PROJECTION_MODE else radius

if distance_2d <= distance_threshold:
    # Backend validation passed
```

**Why keep backend check?**
- Prevents impossible hits (e.g., tip on opposite side of drum set)
- Provides server-side validation for multiplayer scenarios
- Offers fallback if frontend projection fails

#### Phase 3: Handle Edge Cases

1. **Off-screen drums**:
   ```javascript
   // Check if drum is visible (z > 0 in NDC means behind camera)
   if (drumScreen.z > 1 || drumScreen.z < -1) {
     continue; // Skip off-screen drums
   }
   ```

2. **Depth priority** (keep existing logic):
   ```javascript
   // Sort drums by distance to camera (closer drums have priority)
   const sortedDrums = zones.sort((a, b) => {
     const distA = camera.position.distanceTo(
       new THREE.Vector3(...a.pos3d)
     );
     const distB = camera.position.distanceTo(
       new THREE.Vector3(...b.pos3d)
     );
     return distA - distB;
   });
   ```

3. **Perspective distortion compensation**:
   ```javascript
   // Adjust screen radius based on depth to account for perspective
   const depthFactor = 1.0 / (1.0 - drumScreen.z * 0.5);
   const adjustedScreenRadius = screenRadius * depthFactor;
   ```

## Implementation Steps

### Step 1: Update Frontend Collision Detection
- **File**: `static/js/drum_3d.js`
- **Function**: `solveStickCollision()` (lines 376-436)
- **Changes**:
  1. Add Three.js vector projection for tip and drum centers
  2. Calculate 2D screen-space distance
  3. Project drum radius to screen space
  4. Update collision detection to use screen distance
  5. Add depth check to skip off-screen drums

### Step 2: Add Configuration Settings
- **File**: `static/js/3d_settings.js`
- **Changes**:
  1. Add `SCREEN_HIT_RADIUS_OFFSET` constant
  2. Add `USE_CAMERA_PROJECTION` toggle
  3. Add `PERSPECTIVE_DEPTH_FACTOR` for distortion compensation

### Step 3: Relax Backend Validation
- **File**: `drum_collision.py`
- **Function**: `detect_hit_drum()` (lines 356-368)
- **Changes**:
  1. Add `CAMERA_PROJECTION_MODE` flag
  2. Increase distance threshold by 1.5x when camera projection is enabled
  3. Keep existing XZ plane logic as fallback validation

### Step 4: Testing
- Test hitting drums from various angles
- Verify edge drums (Ride, Symbal) are easier to hit when visible on screen
- Ensure no false positives for drums far from view
- Check that backend validation doesn't block legitimate hits

## Expected Behavior Changes

### Before (XZ Plane)
- Hit detection based on overhead view
- Drums at different heights (Y) treated equally
- Visual misalignment: tip appears to miss but registers hit

### After (Camera View)
- Hit detection matches screen appearance
- If tip appears to touch drum on screen → hit registers
- Height differences naturally accounted for by perspective
- More intuitive for player

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Performance impact from projection calculations | Projection is lightweight; calculate only when near drums |
| Backend/frontend desync | Keep backend validation loose; frontend is source of truth |
| Edge case: camera angle changes | Current camera is fixed; if made dynamic, re-calculate on camera move |
| Drums behind camera | Add z-check to skip drums with `z > 1` in NDC |

## Configuration Tunables

After implementation, these can be adjusted for feel:

```javascript
// 3d_settings.js
const SCREEN_HIT_RADIUS_OFFSET = 0.05;  // Increase for easier hits
const PERSPECTIVE_DEPTH_FACTOR = 0.5;   // Adjust depth compensation
const SKIP_OFFSCREEN_DRUMS = true;      // Whether to check off-screen drums
```

## Rollback Plan

If camera projection causes issues:
1. Set `USE_CAMERA_PROJECTION = false` in `3d_settings.js`
2. Code will fall back to existing XZ plane logic
3. No backend changes needed (already compatible)

## Success Criteria

- [ ] Hitting a drum that visually overlaps on screen registers as hit
- [ ] Missing a drum that doesn't overlap on screen doesn't register
- [ ] Edge drums (Ride, Symbal) become easier to hit when in view
- [ ] No false positives for drums far from drumstick
- [ ] Performance remains smooth (60 FPS)
- [ ] Backend validation doesn't block legitimate frontend hits
