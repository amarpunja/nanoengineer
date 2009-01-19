# Copyright 2009 Nanorex, Inc.  See LICENSE file for details. 
"""
cylinder_shader.py - Cylinder shader GLSL source code.

@author: Russ Fish
@version: $Id$
@copyright: 2009 Nanorex, Inc.  See LICENSE file for details.

History:

Russ 090106: Design description file created.
  The most detailed level of items will become comments in the GLSL code.
"""

# See the docstring at the beginning of gl_shaders.py for GLSL references.

# ================================================================
# === Description: GLSL shader program for tapered cylinder/cone primitives,
# === including endcaps and optional halos.
#
# This shader raster-converts analytic tapered cylinders, defined by two
# end-points determining an axis line-segment, and two radii at the end-points.
# A constant-radius cylinder is tapered by perspective anyway, so the same
# shader does cones as well as cylinders.
# 
# The rendered cylinders are smooth, with no polygon facets.  Exact shading, Z
# depth, and normals are calculated in parallel in the GPU for each pixel.
# 
# 
# === Terminology:
# 
# In the remainder of this description, the word "cylinder" will be used to
# refer to the generalized family of tapered cylinders with flat ends
# perpendicular to the axis, including parallel cylinders, truncated cones
# (frusta), and pointed cones where the radius at one end is zero.  (If both
# radii are zero, nothing is visible.)
# 
# The two flat circular end surfaces of generalized cylinders are called
# "endcaps" here, and the rounded middle part a "barrel".  Cylinder barrel
# surfaces are ruled surfaces, made up of straight lines that are referred to as
# "barrel lines".
# 
# The barrel lines and axis line of a cylinder intersect at a "convergence
# point" where the tapered radius goes to zero.  This point will be at an
# infinite distance for an untapered cylinder, in which case its location is a
# pure direction vector, with a W coordinate of zero.  Pairs of barrel lines are
# coplanar, not skew, because they all intersect at the convergence point.
# 
# 
# === How the sphere shader works:
# 
# (This is a quick overview, as context for the cylinder shader.  See the the
# description, comments, and source of the sphere vertex shader program for fine
# details of that process that are not repeated here.)
# 
# The vertex shader for spheres doesn't care what OpenGL "unit" drawing pattern
# is used to bound the necessary pixels in the window, since spheres are
# symmetric in every direction.  Unit cubes, tetrahedra, or viewpoint oriented
# billboard quads are all treated the same.
# 
# . Their vertices are scaled by the sphere radius and added to the sphere
#   center point:
#       drawing_vertex = sphere_center + radius * pattern_vertex
#   This is done in eye coordinates, where lengths are still valid.
# 
# . When perspective is on, a rotation is done as well, to keep a billboard
#   drawing pattern oriented directly toward the viewpoint.
# 
# The fragment (pixel) shader for spheres gets a unit ray vector from the
# rasterizer, and 3D eye-space data from the vertex shader specifying the
# viewpoint and the sphere.  The ray gives the direction from the viewpoint
# through a pixel in the window in the vicinity of the sphere.
# 
# . For ray-hit detection, it determines whether the closest point to the sphere
#   center on the ray is within the sphere radius (or surrounding flat halo disk
#   radius) of the sphere center point.
# 
# . When there is a hit, it calculates the front intersection point of the ray
#   with the sphere, the 3D normal vector there, the depth of the projection
#   onto the window pixel, and the shaded pixel color based on the normal,
#   lights, and material properties.
# 
# 
# === Cylinder shaders:
# 
# Tapered cylinders/cones are more complicated than spheres, but still have
# radial symmetry to work with.  The visible surfaces of a cylinder are the
# portion of the barrel surface towards the viewpoint, and at most one endcap.
# (*Both* endcaps are hidden by the barrel if the viewpoint is anywhere between
# the endcap planes.)
# 
# 
# === How the cylinder vertex shader works:
# 
# A vertex shader is executed in parallel on each input vertex in the drawing
# pattern.  Spheres have a single center point and radius, but (tapered)
# cylinders have two.  All vertices have copies of the associated "attribute"
# values, the two axis endpoints and associated end cap radii, packaged into two
# 4-vector VBOs for efficiency.
# 
# A particular drawing pattern is assumed as the input to this vertex shader, a
# "unit cylinder" quadrilateral billboard with its cylinder axis aligned along
# the X axis: four vertices with X in {0.0,1.0}, Y in {+1.0,-1.0}, and Z is 1.0.
# 
# The vertex shader identifies the individual vertices and handles them
# individually by knowing where they occur in the input drawing pattern.
# 
# This billboard pattern would emerge unchanged as the output for a unit
# cylinder with the viewpoint above the middle of a cylinder, with 1.0 for both
# end radii, and endpoints at [0.0,0.0] and [0.0,1.0].
# 
# In general, the vertices output from the cylinder vertex shader are based on
# the input vertices, scaled and positioned by the cylinder axis taper radii and
# endpoints.  This makes a *symmetric trapezoid billboard quadrilateral*, whose
# midline swivels around the cylinder axis to face directly toward the viewpoint
# *in eye space coordinates*.  The job of this billboard is to cover all of the
# visible pixels of the cylinder barrel and endcap.
# 
# [Further details are below, in the vertex shader main procedure.]
# 
# 
# === A note about pixel (fragment) shaders in general:
# 
# There are a minimum of 32 "interpolators" that smear the "varying" outputs of
# the vertex shader over the pixels during raster conversion, and pass them as
# inputs to the pixel shaders.  Since there are a lot more pixels than vertices,
# everything possible is factored out of the pixel shaders as an optimization.
# 
# . Division is an expensive operation, so denominators of fractions are often
#   passed as inverses for multiplication.
# 
# . Lengths are often passed and compared in squared form (calculated by the
#   dot-product of a vector with itself) to avoid square roots.
# 
# . Trig functions are expensive, but usually implicit in the results of
#   dot-products and cross-products, which are cheap GPU operations.
# 
# 
# === How the cylinder pixel (fragment) shader works:
# 
# Ray-hit detection is in two parts, the endcaps and the barrel surface.
# 
# Endcap circle ray-hit detection is done first, because if the pixel ray hits
# the endcap, it won't get through to the barrel.
# 
# Barrel surface ray-hit detection is based on comparing the "passing distance",
# between the ray line and the cylinder axis line, with the tapered radius of
# the cylinder at the passing point.
# 
# [Further details are below, in the pixel shader main procedure.]
# ===

# <line 0>
# ================================================================
# Note: if texture_xforms is off, a #define N_CONST_XFORMS array dimension is
# prepended to the following.  The #version statement must precede it.
cylinderVertSrc = """
// Vertex shader program for cylinder primitives.
// 
// See the description at the beginning of this file.

// XXX Start by copying a lot of stuff from the sphere shaders, factor later.

// Uniform variables, which are constant inputs for the whole shader execution.
uniform int draw_for_mouseover; // 0:use normal color, 1:glname_color.
uniform int drawing_style;      // 0:normal, 1:override_color, 2:pattern, 3:halo
#define DS_NORMAL 0
#define DS_OVERRIDE_COLOR 1
#define DS_PATTERN 2
#define DS_HALO 3
uniform vec4 override_color;    // Color for selection or highlighted drawing.
uniform int perspective;        // 0:orthographic, 1:perspective.
uniform float ndc_halo_width;   // Halo width in normalized device coords.

uniform int n_transforms;
#ifdef N_CONST_XFORMS
  // Transforms are in uniform (constant) memory. 
  uniform mat4 transforms[N_CONST_XFORMS]; // Must dimension at compile time.
#else
  // Transforms are in texture memory, indexed by a transform slot ID attribute.
  // Column major, one matrix per column: width=N cols, height=4 rows of vec4s.
  // GL_TEXTURE_2D is bound to transform matrices, tex coords in (0...1, 0...1).
  uniform sampler2D transforms;
#endif

// Attribute variables, which are bound to VBO arrays for each vertex coming in.
// Attributes can not be bool or int.
// Each non-matrix attribute has space for up to 4 floating-point values.
attribute mat2x4 endpt_rad;     // Cylinder endpoints and radii.
// The following may be set to constants, when no arrays are provided.
attribute vec4 color;           // Cylinder color and opacity (RGBA).
attribute float transform_id;   // Ignored if zero.  (Attribs cannot be ints.)
attribute vec4 glname_color;    // Mouseover id (glname) as RGBA for drawing.

// Varying outputs, interpolated in the pipeline to the fragment (pixel) shader.
// The varying qualifier can be used only with float, floating-point vectors,
// matrices, or arrays of these.  Structures cannot be varying.
varying vec3 var_ray_vec; // Vertex dir vec (pixel sample vec in frag shader.)
varying vec3 var_view_pt;       // Transformed view point.
varying float var_visible;      // What is visible from the viewpoint.
#define VISIBLE_NOTHING 0.0
#define VISIBLE_BARREL_ONLY 1.0
#define VISIBLE_ENDCAP_ONLY 2.0
#define VISIBLE_ENDCAP_AND_BARREL 3.0
varying float var_visible_endcap; // 0:first endcap visible, 1:second endcap.

// Cylinder data.
varying vec3 var_endpts[2];     // Transformed cylinder endpoints.
varying float var_radii[2];     // Transformed cylinder radii
varying float var_halo_radii[2];// Halo radius at transformed endpt Z depth.
varying vec4 var_basecolor;     // Vertex color.

// Vertex shader main procedure.
void main(void) {

  // Fragment (pixel) color will be interpolated from the vertex colors.
  if (draw_for_mouseover == 1)
    var_basecolor = glname_color;
  else if (drawing_style == DS_OVERRIDE_COLOR)
    // Solid highlighting or selection.
    var_basecolor = override_color;
  else
    var_basecolor = color;
  
  // The endpoints and radii are combined in one attribute: endpt_rad.
  vec4 endpts[2];
  float radii[2];
  int i;
  for (i = 0; i <= 1; i++) {
    endpts[i] = vec4(endpt_rad[i].xyz, 1.0);
    radii[i] = endpt_rad[i].w;      // Per-vertex cylinder radii.
  }

//[ ----------------------------------------------------------------
// Per-primitive transforms.
  mat4 xform;
  if (n_transforms > 0 && int(transform_id) > -1) {
    // Apply a transform, indexed by a transform slot ID vertex attribute.

#ifdef N_CONST_XFORMS
    // Get transforms from a fixed-sized block of uniform (constant) memory.
    // The GL_EXT_bindable_uniform extension allows sharing this through a VBO.
    for (i = 0; i <= 1; i++)
      endpts[i] = transforms[int(transform_id)] * endpts[i];

#else  // texture_xforms.
# if 0 // 1   /// Never check in a 1 value.
    xform = mat4(1.0); /// Testing, override texture xform with identity matrix.
# else
    // Assemble the 4x4 matrix from a column of vec4s stored in texture memory.
    // Map the 4 rows and N columns onto the (0...1, 0...1) texture coord range.
    // The first texture coordinate goes across the width of N matrices.
    float mat = transform_id / float(n_transforms - 1);  // (0...N-1)=>(0...1) .
    // The second tex coord goes down the height of four vec4s for the matrix.
    xform = mat4(texture2D(transforms, vec2(0.0/3.0, mat)),
                 texture2D(transforms, vec2(1.0/3.0, mat)), 
                 texture2D(transforms, vec2(2.0/3.0, mat)), 
                 texture2D(transforms, vec2(3.0/3.0, mat)));
# endif
    for (i = 0; i <= 1; i++)
      endpts[i] = xform * endpts[i];
#endif // texture_xforms.
  }
//] ----------------------------------------------------------------

  // Endpoints and radii in eye space coordinates.
  float billboard_radii[2];   // Either non-haloed, or larger for halos.
  float max_billboard_radius = 0.0;
  for (i = 0; i <= 1; i++) {
    vec4 eye_endpt4 = gl_ModelViewMatrix * endpts[i];
    var_endpts[i] = eye_endpt4.xyz / eye_endpt4.w;

    // Scaled cylinder radii in eye space.  (Assume uniform scale on all axes.)
    vec4 eye_radius4 = gl_ModelViewMatrix * vec4(radii[i], 0.0, 0.0, 0.0);
    float eye_radius = length(vec3(eye_radius4));

    // The non-halo radius.
    var_radii[i] = billboard_radii[i] = eye_radius;

    // For halo drawing, scale up drawing primitive vertices to cover the halo.
    if (drawing_style == DS_HALO) {

      // Take eye-space radius to post-projection units at the endpt depth.
      // Projection matrix does not change the view alignment, just the scale.
      vec4 post_proj_radius4 =
        gl_ProjectionMatrix * vec4(eye_radius, 0.0, var_endpts[i].z, 1.0);
      float post_proj_radius = post_proj_radius4.x / post_proj_radius4.w;

      // Ratio to increase the eye space radius for the halo.
      float radius_ratio = (post_proj_radius + ndc_halo_width)/post_proj_radius;

      // Eye space halo radius for use in the pixel shader.
      var_halo_radii[i] = billboard_radii[i] = radius_ratio * eye_radius;
    }
    max_billboard_radius = max(max_billboard_radius, billboard_radii[i]);
  }

  if (perspective == 1) {
    // In eye space, the origin is at the eye point, by definition.
    var_view_pt = vec3(0.0);
  } else {
    // Without perspective, look from the 2D pixel position, in the -Z dir.
    var_ray_vec = vec3(0.0, 0.0, -1.0);
  }

  //=== Vertex shader details 
  // [See context and general description above, at the beginning of the file.]
  // 
  // Consider a square truncated pyramid, a tapered box with 6 quadrilateral
  // faces, tightly surrounding the tapered cylinder.  It has 2 square faces
  // containing circular endcaps, and 4 symmetric trapezoids (tapered rectangles
  // with 2 parallel edges) tangent to cylinder barrel-lines along their
  // midlines and connecting the endcap squares.
  //===

  // The cylinder axis and the taper interpolated along it, in eye space units.
  vec3 axis_line_vec = var_endpts[1] - var_endpts[0];
  vec3 axis_line_dir = normalize(axis_line_vec);
  float axis_length = length(axis_line_vec);
  float axis_radius_taper = (billboard_radii[1] - billboard_radii[0])
                            / axis_length;

  //===
  // . The shader determines our position vs. the endcap planes by projecting
  //   the viewpoint onto the cylinder axis line, and comparing to the locations
  //   along the axis line of the cylinder endpoints.
  //===

  bool vp_between_endcaps;
  float vp_axis_proj_len; // Used for perspective only.
  int visible_endcap;
  if (perspective == 1) {

    // (Note: axis_line_dir vector is normalized, viewpt to endpt vec is not.)
    vp_axis_proj_len = dot(axis_line_dir, var_view_pt - var_endpts[0]);
    vp_between_endcaps = vp_axis_proj_len >= 0.0 &&       // First endpoint.
                         vp_axis_proj_len <= axis_length; // Second endpoint.
    // (Only valid when not between endcap planes, where no endcap is visible.)
    visible_endcap = int(vp_axis_proj_len < 0.0);

  } else {

    // In orthogonal projection, if the axis is very nearly in the XY plane, the
    // endcaps are nearly edge-on and are ignored.  Otherwise, the one with the
    // greater Z is the visible one.
    vp_between_endcaps = abs(var_endpts[1].z - var_endpts[0].z) < 0.001;
    visible_endcap = int(var_endpts[1].z > var_endpts[0].z);

  }
  var_visible_endcap = float(visible_endcap); // Varyings are always floats.

  //===
  // . The viewpoint is inside the barrel surface if the distance to its
  //   projection onto the cylinder axis is less than the cylinder radius,
  //   extrapolated along the axis, at that projection point.
  //===

  bool vp_in_barrel;
  vec3 endpt_toward_vp_dir[2], endpt_across_vp_dir[2];
  if (perspective == 1) {

    vec3 vp_axis_proj_pt = var_endpts[0] + vp_axis_proj_len * axis_line_dir;
    float vp_axis_dist = length(vp_axis_proj_pt - var_view_pt);
    float vp_cyl_radius = vp_axis_proj_len * axis_radius_taper;
    vp_in_barrel = vp_axis_dist < vp_cyl_radius;

    // Directions relative to the viewpoint, perpendicular to the cylinder axis
    // at the endcaps, for constructing swiveling trapezoid billboard vertices.
    for (i = 0; i <= 1; i++) {
     if (vp_axis_dist < 0.001) {
        // Special case when looking straight down the axis.
        endpt_across_vp_dir[i] = vec3(1.0, 0.0, 0.0);
        endpt_toward_vp_dir[i] = vec3(0.0, 1.0, 0.0);
      } else {
        vec3 vp_endpt_dir = normalize(var_endpts[i] - var_view_pt);

        // Perpendicular to axis at endpt, in the plane of axis and viewpt.
        endpt_across_vp_dir[i] = cross(axis_line_dir, vp_endpt_dir);

        // Perpendicular to both the axis and the across_vp 
        endpt_toward_vp_dir[i] = cross(axis_line_dir, endpt_toward_vp_dir[i]);
      }
    }
    
  } else {

    int near_end = int(var_endpts[1].z > var_endpts[0].z);
    int far_end = 1-near_end;
    float radius_diff = var_radii[near_end] - var_radii[far_end];
    float axis_offset = length(var_endpts[near_end].xy-var_endpts[far_end].xy);
    vp_in_barrel =  radius_diff >= 0.0 && axis_offset <= radius_diff;
                   
    // Directions relative to the view dir, perpendicular to the cylinder axis,
    // for constructing swiveling trapezoid billboard vertices.
   if (axis_offset < 0.001) {
      // Special case when looking straight down the axis.
      endpt_across_vp_dir[0] = endpt_across_vp_dir[1] = vec3(1.0, 0.0, 0.0);
      endpt_across_vp_dir[0] = endpt_across_vp_dir[1] = vec3(0.0, 1.0, 0.0);
    } else {
      // Perpendicular to cylinder axis and the view direction.
      endpt_across_vp_dir[i] = cross(axis_line_dir, var_ray_vec);

      // Perpendicular to both the axis and the endpt_across_vp_dir.
      endpt_toward_vp_dir[i] = cross(axis_line_dir, endpt_toward_vp_dir[i]);
    }

  }

  //===
  // The output vertices for the billboard quadrilateral are based on the
  // vertices of the tapered box, with several cases:
  // 
  // . NE1 does not draw the interior (back sides) of atom and bond surfaces.
  //   When the viewpoint is both (1) between the endcap planes, *and* (2)
  //   inside the barrel surface as well, we draw nothing at all.
  //===

  // Output vertex in eye space for now, will be projected into clipping coords.
  vec3 billboard_vertex;  

  if (vp_between_endcaps && vp_in_barrel) {
    var_visible = VISIBLE_NOTHING;
    billboard_vertex = vec3(0.0, 0.0, -1.0); // Could be anything (nonzero?)
  }

  //===
  // . When the viewpoint is inside the extension of the barrel surface, only
  //   one endcap is visible, so the output billboard is the square endcap face
  //   whose normal (along the cylinder axis) is toward the viewpoint.
  //===

  else if (vp_in_barrel) {
    // Just the single visible endcap in this case.
    var_visible = VISIBLE_ENDCAP_ONLY;
    vec3 scaled_across = billboard_radii[visible_endcap]
                         * endpt_across_vp_dir[visible_endcap];
    vec3 scaled_toward = billboard_radii[visible_endcap]
                         * endpt_toward_vp_dir[visible_endcap];

    // The unit rectangle drawing pattern is 0 to 1 in X, elsewhere
    // corresponding to the direction along the cylinder axis, but here we are
    // looking only at the endcap square, and so adjust to +-1 in X.
    billboard_vertex = var_endpts[visible_endcap]
      + (gl_Vertex.x * 2.0 - 1.0) * scaled_across
      + gl_Vertex.y * scaled_toward;
  }

  //===
  // . When the viewpoint is between the endcap planes, the output billboard is
  //   only a barrel face trapezoid (made of vertices from the two edges of the
  //   endcap squares that are toward the viewpoint) because the endcaps are
  //   hidden by the barrel.  We swivel the pyramid on its axis to align a
  //   barrel face with the viewpoint vector; we only need one barrel face
  //   because it hides all the others.
  //===

  else if (vp_between_endcaps) {
    var_visible = VISIBLE_BARREL_ONLY;
    // Connecting two endcaps, X identifies which one this vertex comes from.
    int endcap = int(gl_Vertex.x);
    vec3 scaled_across = billboard_radii[endcap] * endpt_across_vp_dir[endcap];
    vec3 scaled_toward = billboard_radii[endcap] * endpt_toward_vp_dir[endcap];
    billboard_vertex = var_endpts[endcap]
      + scaled_toward  // Offset to  the pyramid face toward the viewpoint.
      + gl_Vertex.y * scaled_across;
  }

  //===
  // . When *both a barrel and an endcap* are visible, an endcap square face and
  //   a barrel face are combined into a single trapezoid by ignoring the shared
  //   edge between them, replacing an 'L' shaped combination with a diagonal
  //   '\'.
  // 
  //   - A subtlety: the max of the two cylinder radii is used for the endcap
  //     square size, because the far end of the cylinder barrel may have a
  //     larger radius than the endcap circle toward us, and we want to cover it
  //     too.  (Tighter bounding trapezoids are probably possible, but likely
  //     more work to compute, and would make no difference most of the time
  //     since ray-hit pixel discard is quick.)
  //===

  else {
    // Connect the outer edge of the visible endcap face with the inner edge of
    // the hidden endcap face at the other end of the cylinder barrel.
    var_visible = VISIBLE_ENDCAP_AND_BARREL;
    int endcap = int(gl_Vertex.x);
    vec3 scaled_across = max_billboard_radius * endpt_across_vp_dir[endcap];
    vec3 scaled_toward = max_billboard_radius * endpt_toward_vp_dir[endcap];
    billboard_vertex = var_endpts[endcap]
      + (endcap == visible_endcap ? -1.0 : 1.0 ) * scaled_toward
      + gl_Vertex.y * scaled_across;
  }

  if (perspective == 1) {
    // With perspective, look from the origin, toward the vertex (pixel) points.
    var_ray_vec = normalize(billboard_vertex);
  } else {
    // Without perspective, look from the 2D pixel position, in the -Z dir.
    var_view_pt = vec3(billboard_vertex.xy, 0.0);  
  }

  // Transform the billboard vertex through the projection matrix, making clip
  // coordinates for the next stage of the pipeline.
  gl_Position = gl_ProjectionMatrix * vec4(billboard_vertex, 1.0);
}
"""

# ================================================================
# <line 0>
cylinderFragSrc = """
// Fragment (pixel) shader program for cylinder primitives.
// 
// See the description at the beginning of this file.

// requires GLSL version 1.20
#version 120

// Uniform variables, which are constant inputs for the whole shader execution.
uniform int draw_for_mouseover; // 0: use normal color, 1: glname_color.
uniform int drawing_style;      // 0:normal, 1:override_color, 2:pattern, 3:halo
#define DS_NORMAL 0
#define DS_OVERRIDE_COLOR 1
#define DS_PATTERN 2
#define DS_HALO 3
uniform vec4 override_color;    // Color for selection or highlighted drawing.
uniform float override_opacity; // Multiplies the normal color alpha component.

// Lighting properties for the material.
uniform vec4 material; // Properties: [ambient, diffuse, specular, shininess].

// Uniform variables, which are constant inputs for the whole shader execution.
uniform int perspective;
uniform vec4 clip;              // [near, far, middle, depth_inverse]

uniform vec4 intensity;    // Set an intensity component to 0 to ignore a light.

// A fixed set of lights.
uniform vec3 light0;
uniform vec3 light1;
uniform vec3 light2;
uniform vec3 light3;

uniform vec3 light0H;           // Blinn/Phong halfway/highlight vectors.
uniform vec3 light1H;
uniform vec3 light2H;
uniform vec3 light3H;

// Inputs, interpolated by raster conversion from the vertex shader outputs.
// The varying qualifier can be used only with float, floating-point vectors,
// matrices, or arrays of these.  Structures cannot be varying.
varying vec3 var_ray_vec; // Pixel sample vec (vertex dir vec in vert shader.)
varying vec3 var_view_pt;       // Transformed view point.

varying float var_visible;      // What is visible from the viewpoint.
#define VISIBLE_NOTHING 0.0
#define VISIBLE_BARREL_ONLY 1.0
#define VISIBLE_ENDCAP_ONLY 2.0
#define VISIBLE_ENDCAP_AND_BARREL 3.0
varying float var_visible_endcap; // 0:first endcap visible, 1:second endcap.

// Cylinder data.
varying vec3 var_endpts[2];     // Transformed cylinder endpoints.
varying float var_radii[2];     // Transformed cylinder radii
varying float var_halo_radii[2];// Halo radius at transformed endpt Z depth.

varying vec4 var_basecolor;     // Vertex color.

// Line functions; assume line direction vectors are normalized (unit vecs.)
vec3 pt_proj_onto_line(in vec3 point, in vec3 pt_on_line, in vec3 line_dir) {
  // Add the projection along the line direction, to a base point on the line.
  return pt_on_line + dot(line_dir, point - pt_on_line) * line_dir;
}
float pt_dist_from_line(in vec3 point, in vec3 pt_on_line, in vec3 line_dir) {
  // (The length of of the cross-product is the sine of the angle between two
  // vectors, times the lengths of the vectors.  Sine is opposite / hypotenuse.)
  return length(cross(point - pt_on_line, line_dir));
}
float pt_dist_sq_from_line(in vec3 point, in vec3 pt_on_line, in vec3 line_dir){
  // Avoid a sqrt when we are just going to square the length anyway.
  vec3 crossprod = cross(point - pt_on_line, line_dir);
  return dot(crossprod, crossprod);
}

// Fragment (pixel) shader main procedure.
void main(void) {
  // This is all in *eye space* (pre-projection camera coordinates.)

  // Nothing to do if the viewpoint is inside the cylinder.
  if (var_visible == VISIBLE_NOTHING)
    discard; // **Exit**

  // Vertex ray direction vectors were interpolated into pixel ray vectors.
  // These go from the view point, through a sample point on the drawn polygon,
  // *toward* the cylinder (but may miss it and be discarded.)
  vec3 ray_line_dir = normalize(var_ray_vec);// Interpolation denormalizes vecs.

  // The cylinder axis and taper interpolated along it, in eye space units.
  // XXX These are known in the vertex shader; consider making them varying.
  vec3 endpt_0 = var_endpts[0];
  vec3 axis_line_vec = var_endpts[1] - endpt_0;
  vec3 axis_line_dir = normalize(axis_line_vec);
  float axis_length = length(axis_line_vec);
  float axis_radius_taper = (var_radii[1] - var_radii[0]) / axis_length;

  //=== Fragment (pixel) shader details
  // [See context and general description above, at the beginning of the file.]
  // 
  // The ray and axis lines in general do not intersect.  The closest two
  // points where a pair of skew lines pass are their intersections with the
  // line that crosses perpendicular to both of them.  The direction vector of
  // this passing-line is the cross-product of the two line directions.
  // Project a point on each line onto the passing-line direction with a
  // dot-product, and take the distance between them with another dot-product.
  //===

  // The direction of the passing line is from the axis line to the ray line.
  // With normalized inputs, the length is the sine of the angle between them.
  vec3 passing_line_crossprod = cross(ray_line_dir, axis_line_dir);
  vec3 passing_line_dir = normalize(passing_line_crossprod);

  // The distance between the passing points is the projection of the vector
  // between two points on the two lines (the viewpoint on the ray line, and a
  // cylinder endpoint on the axis line) onto the passing-line direction vector.
  float passing_pt_dist = dot(passing_line_dir, var_view_pt - endpt_0);

  // The vector between the passing points, from the axis to the ray.
  vec3 passing_pt_vec = passing_pt_dist * passing_line_dir;

  // Project the first cylinder endpoint onto the plane containing the ray from
  // the viewpoint, and perpendicular to the passing_line at the ray_passing_pt.
  vec3 ep0_proj_pt = endpt_0 + passing_pt_vec;

  // Project the viewpoint onto a line through the above point, parallel to
  // the cylinder axis, and going through through the ray_passing_pt we want.
  vec3 vp_proj_pt = pt_proj_onto_line(var_view_pt, ep0_proj_pt, axis_line_dir);
  // Distance from the viewpoint to its projection.
  float vp_proj_dist = length(vp_proj_pt - var_view_pt);

  // Now we have a right triangle with the right angle where the viewpoint was
  // projected and can compute the ray_passing_pt.
  //  * The hypotenuse is along the ray from the viewpoint to the passing point.
  //  * The sine of the angle there between the ray and axis line directions is
  //    the length of the cross product vector.
  //  * The side opposite the angle goes from the viewpoint to its projection.
  //  * So the (signed) length of the adjacent side, from the projected point to
  //    the ray_passing_pt, is the length of the opposite side over the sine.
  float proj_passing_dist = vp_proj_dist / length(passing_line_crossprod);
  vec3 ray_passing_pt = vp_proj_pt + proj_passing_dist * axis_line_dir;

  // Project down to the plane containing the axis for the other passing point.
  vec3 axis_passing_pt = ray_passing_pt - passing_pt_vec;
  vec3 vp_axis_proj_pt = vp_proj_pt - passing_pt_vec;

  //===
  // Endcap circle ray-hit detection is done first, because if the pixel ray
  // hits the endcap, it will not get through to the barrel.
  //===

  vec3 ray_hit_pt;      // For ray-hit and depth calculations.
  vec3 normal;          // For shading calculation.

  bool endcap_hit = false;
  bool halo_hit = false;
  int visible_endcap = int(var_visible_endcap); // Varyings are always floats.

  // Skip if no endcap is visible.
  if (var_visible != VISIBLE_BARREL_ONLY) { // (Never VISIBLE_NOTHING.)
    // (VISIBLE_ENDCAP_ONLY or VISIBLE_ENDCAP_AND_BARREL.)

    //===
    // . The endcap ray-hit test is similar to the sphere shader hit test, in
    //   that a center point and a radius are given, so calculate the distance
    //   that the ray passes from the endcap center point similarly.
    // 
    // . The difference is that the endcaps are flat circles, not spheres,
    //   projecting to an elliptical shape in general.  We deal with that by
    //   intersecting the ray with the endcap plane and comparing the distance
    //   in the plane.  (Tweaked for halos as in the sphere shader.)
    //===

    // Interpolate the intersection of the ray with the endcap plane, between
    // the projection of the viewpoint onto the axis, and the ray_passing_pt.
    ray_hit_pt = mix(var_view_pt, ray_passing_pt,
      length(var_endpts[visible_endcap] - vp_axis_proj_pt) /
        length(ray_passing_pt - vp_axis_proj_pt));

    // Is the intersection within the endcap radius from the endpoint?
    vec3 closest_vec = ray_hit_pt - var_endpts[visible_endcap];
    float plane_closest_dist = length(closest_vec);
    if (plane_closest_dist <= var_radii[visible_endcap]) {

      // Hit the endcap.  The normal is the axis direction, pointing outward.
      endcap_hit = true;
      normal = axis_line_dir * float(visible_endcap * 2 - 1); // * -1 or +1.

    } else if (drawing_style == DS_HALO &&
               plane_closest_dist <= var_halo_radii[visible_endcap]) {

      // Missed the endcap, but hit an endcap halo.
      halo_hit = endcap_hit = true;

    } else if (var_visible == VISIBLE_ENDCAP_ONLY ) {

      // Early out.  We know only an endcap is visible, and we missed it.
      discard; // **Exit**

    }      
  }

  // Skip if we already hit an endcap. (Never VISIBLE_NOTHING here.)
  if (! endcap_hit && var_visible != VISIBLE_ENDCAP_ONLY) {
    // (VISIBLE_BARREL_ONLY, or VISIBLE_ENDCAP_AND_BARREL but missed endcap.)

    //===
    // Barrel surface ray-hit detection is based on comparing the 'passing
    // distance', between the the ray line and the cylinder axis line, with the
    // tapered radius of the cylinder at the passing point.
    // 
    // . Interpolate the tapered radius along the axis line, to the point
    //   closest to the ray on the cylinder axis line, and compare with the
    //   passing distance.
    //===

    float ep0_app_dist = length(axis_passing_pt - endpt_0);
    float passing_radius = axis_radius_taper * ep0_app_dist;
    if (passing_pt_dist > passing_radius) {

      // Missed the edge of the barrel, but might still hit a halo on it.
      float halo_radius_taper = (var_halo_radii[1] - var_halo_radii[0])
                                / axis_length;
      float passing_halo_radius = halo_radius_taper * ep0_app_dist;
      halo_hit = drawing_style == DS_HALO &&
                 passing_pt_dist <= passing_halo_radius;
      if (halo_hit) {

        // The ray_passing_pt is beyond the edge of the cylinder barrel, but
        // it is on the passing-line, perpendicular to the ray.  Perfect.
        ray_hit_pt = ray_passing_pt;

      } else {

        // Nothing more to do when we miss the barrel of the cylinder entirely.
        discard; // **Exit**

      }
    }

    //===
    // We already know that the viewpoint is not within the cylinder (above, in
    // the vertex shader), so if the ray from the viewpoint to the pixel passes
    // within the cylinder radius of the axis line, it has to come in from
    // outside, intersecting the extended barrel of the cylinder.  We will have
    // a hit if the projection of this intersection point onto the axis line
    // lies between the endpoints of the cylinder.
    // 
    // The pixel-ray goes from the viewpoint toward the pixel we are shading,
    // intersecting the cylinder barrel, passing closest to the axis-line inside
    // the barrel, and intersecting the barrel again on the way out.  We want
    // the ray-line vs. barrel-line intersection that is closest to the
    // viewpoint.  (Note: The two intersection points and the ray passing-point
    // will all be the same point when the ray is tangent to the cylinder.)
    // 
    // . First, we find a point on the barrel line that contains the
    //   intersection, in the cross-section plane of the cylinder.  This
    //   crossing-plane is perpendicular to the axis line and contains the two
    //   closest passing points, as well as the passing-line perpendicular to
    //   the axis of the cylinder.
    // 
    //   If the radii are the same at both ends of the cylinder, the
    //   barrel-lines are parallel.  The projection of the ray-line, along a
    //   ray-plane *parallel to the cylinder axis* into the crossing-plane, is
    //   perpendicular to the passing-line at the ray passing-point, both of
    //   which we already have.
    //===

    // (The 'cpl_' prefix is used for objects in the cross-section plane.)
    vec3 cpl_proj_view_pt, cpl_passing_pt;
    float cpl_passing_dist_sq, cpl_radius_sq;
    vec3 convergence_pt;  // Only used for tapered cylinders.

    // Untapered cylinders.
    if (var_radii[0] == var_radii[1]) {
      cpl_proj_view_pt = var_view_pt + proj_passing_dist * axis_line_dir;
      cpl_passing_pt = ray_passing_pt;
      cpl_passing_dist_sq = passing_pt_dist * passing_pt_dist;
      cpl_radius_sq = var_radii[0] * var_radii[0];

    } else {

      // Tapered cylinders.

      //===
      //   If the cylinder radii differ, instead project the viewpoint and the
      //   ray-line direction vector into the cross-plane *toward the
      //   convergence-point*, scaling by the taper of the cylinder along the
      //   axis.  [This is the one place where tapered cylinders and cones are
      //   handled differently.]
      //   
      //   - Note: If we project parallel to the axis without tapering toward
      //     the convergence-point, we are working in a plane parallel to the
      //     cylinder axis, which intersects a tapered cylinder or cone in a
      //     hyperbola.  Intersecting a ray with a hyperbola is hard.  Instead,
      //     we arrange to work in a plane that includes the convergence point,
      //     so the intersection of the plane with the cylinder is two straight
      //     lines.  Lines are easy.
      // 
      //   - The ray-line and the convergence-point determine a ray-plane, with
      //     the projected ray-line at the intersection of the ray-plane with
      //     the cross-plane.  If the ray-line goes through (i.e. within one
      //     pixel of) the convergence-point, we instead discard the pixel.
      //     Right at the tip of a cone, the normal sample is very unstable, so
      //     we can not do valid shading there anyway.
      //===

      // Distance to the convergence point where the radius tapers to zero,
      // along the axis from the first cylinder endpoint.
      float ep0_cp_axis_dist = var_radii[0] / axis_radius_taper;
      
      convergence_pt = endpt_0 + ep0_cp_axis_dist * axis_line_dir;

      float ray_cpt_dist = dot(convergence_pt - var_view_pt, ray_line_dir);
      if (ray_cpt_dist <= .001) // XXX Approximation; should be in NDC coords.
            discard; // **Exit**

      //===
      //   - We calculate a *different 2D ray-line passing-point*, and hence
      //     passing-line, for tapered cylinders and cones.  It is the closest
      //     point, on the *projected* ray-line in the cross-plane, to the
      //     cylinder axis passing-point (which does not move.)
      //     
      //     Note: The original passing-point is still *also* on the projected
      //     ray-line, but not midway between the projected barrel-line
      //     intersections anymore.  In projecting the ray-line into the
      //     crossing-plane within the ray-plane, the passing-line twists around
      //     the cylinder axis.  You can see this from the asymmetry of the
      //     tapering barrel-lines in 3D.  The ray-line/barrel-line intersection
      //     further from the convergence-point has to travel further to the
      //     crossing-plane than the nearer one.  (Of course, we do not *know*
      //     those points yet, we are in the process of computing one of them.)
      //===

      // Interpolate the viewpoint to the crossing-plane, along the line-segment
      // from the viewpoint to the convergence point, with a ratio along the
      // axis from the projected viewpoint, to the axis passing point, to the
      // convergence point.
      cpl_proj_view_pt = mix(var_view_pt, convergence_pt,
        proj_passing_dist / length(convergence_pt - vp_axis_proj_pt));

      // New passing point.
      vec3 cpl_ray_line_dir = normalize(ray_passing_pt - cpl_proj_view_pt);
      cpl_passing_pt = pt_proj_onto_line(axis_passing_pt,
        cpl_proj_view_pt, cpl_ray_line_dir);

      cpl_passing_dist_sq = pt_dist_sq_from_line(axis_passing_pt,
        cpl_proj_view_pt, cpl_ray_line_dir);

      cpl_radius_sq = passing_radius * passing_radius;

    }
    
    //===
    //   [Now we are back to common code for tapered and untapered cylinders.]
    // 
    //   - In the cross-plane, the projected ray-line intersects the circular
    //     cross section of the cylinder at two points, going through the ray
    //     passing-point, and cutting off a chord of the line and an arc of the
    //     circle.  Two barrel lines go through the intersection points, along
    //     the surface of the cylinder and also in the ray-plane.  Each of them
    //     contains one of the intersection points between the ray and the
    //     cylinder.
    // 
    //     . The chord of the projected ray-line is perpendicularly bisected by
    //       the passing-line, making a right triangle in the cross-plane.
    // 
    //     . The passing-distance is the length of the base of the triangle on
    //       the passing-line, adjacent to the cylinder axis point.
    // 
    //     . The cylinder cross-section circle radius, tapered along the
    //       cylinder to the cross-plane, is the length of the hypotenuse,
    //       between the axis point and the first intersection point of the ray
    //       chord with the circle.
    // 
    //     . The length of the right triangle side opposite the axis, along the
    //       chord of the ray-line toward the viewpoint, is given by the
    //       Pythagorean Theorem.  This locates the third vertex of the
    //       triangle, in the cross-plane and the ray-plane.
    //===

    vec3 barrel_line_pt = cpl_passing_pt +
      sqrt(cpl_radius_sq - cpl_passing_dist_sq)
        * normalize(cpl_proj_view_pt - cpl_passing_pt);

    //===
    //     . The barrel line we want passes through the cross-plane at that
    //       point as well as the convergence-point (which is at infinity in the
    //       direction of the axis for an untapered cylinder.)
    //===

    vec3 barrel_line_dir = axis_line_dir;
    if (var_radii[0] != var_radii[1])
      barrel_line_dir = normalize(convergence_pt - barrel_line_pt);

    //===
    // . Intersect the 3D ray-line with the barrel line in the ray-plane, giving
    //   the 3D ray-cylinder intersection point.  Note: this is not in general
    //   contained in the 2D crossing-plane, depending on the location of the
    //   viewpoint.
    // 
    //   - The intersection point may be easily calculated by interpolating two
    //     points on the ray line (e.g. the viewpoint and the ray
    //     passing-point.)  The interpolation coefficients are the ratios of
    //     their projection distances to the barrel line.  (More dot-products.)
    //===

    float vp_bl_proj_dist = pt_dist_from_line(var_view_pt,
                                              barrel_line_pt, barrel_line_dir);

    float bl_cpp_proj_dist = pt_dist_from_line(cpl_passing_pt,
                                               barrel_line_pt, barrel_line_dir);

    ray_hit_pt = mix(var_view_pt, cpl_passing_pt,
      vp_bl_proj_dist / (vp_bl_proj_dist + bl_cpp_proj_dist));

    //===
    // . Project the intersection point onto the axis line to determine whether
    //   we hit the cylinder between the endcap planes.  If so, calculate the
    //   barrel-line normal.
    //===
    
    float ip_axis_proj_len = dot(axis_line_dir, ray_hit_pt - endpt_0);
    if (ip_axis_proj_len < 0.0 || ip_axis_proj_len > axis_length) {

      // We missed the portion of the cylinder barrel between the endcap planes.
      // A halo may be required past the end.  We try endcap hits *before* the
      // barrel, so we know there is not one providing a halo on this end yet.
      halo_hit = drawing_style == DS_HALO &&
          (ip_axis_proj_len < 0.0 &&
             ip_axis_proj_len >= var_radii[0] - var_halo_radii[0] ||
           ip_axis_proj_len > axis_length &&
             ip_axis_proj_len <= axis_length + var_halo_radii[1] - var_radii[1]
          );

      if (! halo_hit)
        discard; // **Exit**

    } else {

      //===
      //   - The normal at the intersection point (and all along the same barrel
      //     line) is *perpendicular to the barrel line* (not the cylinder
      //     axis), in the radial plane containing the cylinder axis and the
      //     barrel line.
      // 
      //   - The cross-product of the axis-intersection vector (from the
      //     intersection point toward the axis passing-point), with the
      //     barrel-line direction vector (from the first cylinder endpoint
      //     toward the second) makes a vector tangent to the cross-plane
      //     circle, pointed along the arc toward the passing-line.
      // 
      //   - The cross-product of the tangent-vector, with the barrel-line
      //     direction vector, makes the normal to the cylinder along the barrel
      //     line.
      //==

      vec3 arc_tangent_vec = cross(axis_passing_pt - ray_hit_pt,
                                   barrel_line_dir);
      normal = normalize(cross(arc_tangent_vec, barrel_line_dir));
    }
  }

  // Distance from the view point to the intersection, transformed into
  // normalized device coordinates, sets the fragment depth.  (Note: The
  // clipping box depth is passed as its inverse, to save a divide.)
  float sample_z = ray_hit_pt.z;
  if (perspective == 1) {
    // Perspective: 0.5 + (mid + (far * near / sample_z)) / depth
    gl_FragDepth = 0.5 + (clip[2] + (clip[1] * clip[0] / sample_z)) * clip[3];
  } else {
    // Ortho: 0.5 + (-middle - sample_z) / depth
    gl_FragDepth = 0.5 + (-clip[2] - sample_z) * clip[3];
  }

  // Nothing more to do if the intersection point is clipped.
  if (gl_FragDepth < 0.0 || gl_FragDepth > 1.0)
      discard; // **Exit**

  // No shading or lighting on halos.
  if (! halo_hit) {
      gl_FragColor = override_color; // No shading or lighting on halos.
  } else {

    // Shading control, from the material and lights.
    float ambient = material[0];

    // Accumulate diffuse and specular contributions from the lights.
    float diffuse = 0.0;
    diffuse += max(0.0, dot(normal, light0)) * intensity[0];
    diffuse += max(0.0, dot(normal, light1)) * intensity[1];
    diffuse += max(0.0, dot(normal, light2)) * intensity[2];
    diffuse += max(0.0, dot(normal, light3)) * intensity[3];
    diffuse *= material[1]; // Diffuse intensity.

    // Blinn highlight location, halfway between the eye and light vecs.
    // Phong highlight intensity: Cos^n shinyness profile.  (Unphysical.)
    float specular = 0.0;
    float shininess = material[3];
    specular += pow(max(0.0, dot(normal, light0H)), shininess) * intensity[0];
    specular += pow(max(0.0, dot(normal, light1H)), shininess) * intensity[1];
    specular += pow(max(0.0, dot(normal, light2H)), shininess) * intensity[2];
    specular += pow(max(0.0, dot(normal, light3H)), shininess) * intensity[3];
    specular *= material[2]; // Specular intensity.

    // Do not do lighting while drawing glnames, just pass the values through.
    if (draw_for_mouseover == 1)
      gl_FragColor = var_basecolor;
    else if (drawing_style == DS_OVERRIDE_COLOR)
      // Highlighting looks 'special' without shinyness.
      gl_FragColor = vec4(var_basecolor.rgb * vec3(diffuse + ambient),
                          1.0);
    else
      gl_FragColor = vec4(var_basecolor.rgb * vec3(diffuse + ambient) +
                            vec3(specular),   // White highlights.
                          var_basecolor.a * override_opacity);
  }
}
"""
