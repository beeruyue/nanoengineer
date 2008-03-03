// Copyright 2008 Nanorex, Inc.  See LICENSE file for details.

#ifndef NX_SCENEGRAPH_OPENGL_H
#define NX_SCENEGRAPH_OPENGL_H

// Scenegraph classes for OpenGL

#if defined(__APPLE__)
#include <OpenGL/gl.h>
#else
#include <GL/gl.h>
#endif

#include <cstring>

#include "Nanorex/Interface/NXSceneGraph.h"
#include "Nanorex/Utility/NXUtility.h"
#include "Nanorex/Utility/NXCommandResult.h"
#include "NXOpenGLMaterial.h"


namespace Nanorex {

/* CLASS: NXSGOpenGLNode */
/**
 * Base-class for all OpenGL scenegraph nodes. Helps to maintain debug checks
 * for OpenGL state like matrix-stack depth etc.
 *
 * @ingroup NanorexInterface, PluginArchitecture, GraphicsArchitecture
 */
class NXSGOpenGLNode : public NXSGNode {
public:
    NXSGOpenGLNode() : modelViewStackDepth(0) {}
    ~NXSGOpenGLNode() {}
    
    /// Prevent addition of generic nodes so that children are OpenGL
    /// scenegraph nodes. Required to be able to propagate context checks
    bool addChild(NXSGNode *const child);
    
    /// Add child if OpenGL state limits are not exceeded
    virtual bool addChild(NXSGOpenGLNode *const child);
    
    int getModelViewStackDepth(void) { return modelViewStackDepth; }
    
    /// Called by parent when its stack depth is updated to recursively
    /// propagate this info to leaves
    virtual bool newParentModelViewStackDepth(int newMVStackDepth);
    
    // static members
    
    /// Assess OpenGL context limits.
    /// Must be called after the OpenGL context is made current and
    /// before OpenGL scenegraph module is used
    bool InitializeContext(void);
    
    /// Last error in the context
    static NXCommandResult* GetContextError(void) { return &commandResult; }
    
    static GLint const& GetMaxModelViewStackDepth(void)
    { return _s_maxModelViewStackDepth; }
    
protected:
    /// Maximum model-view stack depth in reaching this node from root
    int modelViewStackDepth;
    
    // -- OpenGL context -- 
    
    /// model-view stack-size limit
    static GLint _s_maxModelViewStackDepth;
    
    /// Most recent error - to be set by failing node
    /// All calling nodes propagate boolean result back up to root
    static NXCommandResult commandResult;
    
    static void SetError(int errCode, char const *const errMsg);
};


/* CLASS: NXSGOpenGLTransform */
/**
 * Base class for OpenGL transforms
 * Re-implements the applyRecursive() method so that it pushes the modelview
 * matrix before applying the scenegraph subtree, and pops the modelview
 * matrix afterwards.
 *
 * @ingroup NanorexInterface, PluginArchitecture, GraphicsArchitecture
 */
class NXSGOpenGLTransform : public NXSGOpenGLNode {
public:
    NXSGOpenGLTransform() throw () {}
    ~NXSGOpenGLTransform() throw () {};
};


/* CLASS: NXSGOpenGLModelViewTransform */
/**
 * Base class for OpenGL transforms that affect the modelview matrix
 *
 * @ingroup NanorexInterface, PluginArchitecture, GraphicsArchitecture
 */
class NXSGOpenGLModelViewTransform : public NXSGOpenGLTransform {
public:
    NXSGOpenGLModelViewTransform() throw()
        : NXSGOpenGLTransform()
    { ++modelViewStackDepth; /* must be >= 1 */ }
    
    ~NXSGOpenGLModelViewTransform() throw() {}
    
    bool addChild(NXSGOpenGLNode *child);
    
    /// Re-implement base-class method because this class increments
    /// model-view stack-depth
    bool newParentModelViewStackDepth(int parentMVStackDepth);
    
    bool applyRecursive(void) const throw();
    
    void deleteRecursive(void) { }
};


/* CLASS NXSGOpenGLTranslate */
/**
 * OpenGL translation node
 *
 * @ingroup NanorexInterface, PluginArchitecture, GraphicsArchitecture
 */
class NXSGOpenGLTranslate : public NXSGOpenGLModelViewTransform {
public:
    NXSGOpenGLTranslate(double const& the_x,
                        double const& the_y,
                        double const& the_z) throw ()
        : x(the_x), y(the_y), z(the_z) {}
    ~NXSGOpenGLTranslate() throw () {}
    bool apply(void) const throw ();
private:
    GLdouble x, y, z;
};



/* CLASS: NXSGOpenGLRotate */
/**
 * Scenegraph rotation node
 *
 * @ingroup NanorexInterface, PluginArchitecture, GraphicsArchitecture
 */
class NXSGOpenGLRotate : public NXSGOpenGLModelViewTransform {
public:
    NXSGOpenGLRotate(double const& the_angle,
                     double const& the_x,
                     double const& the_y,
                     double const& the_z) throw ()
        : angle(the_angle), x(the_x), y(the_y), z(the_z) {}
    ~NXSGOpenGLRotate() throw () {}
    bool apply(void) const throw ();
private:
    GLdouble angle, x, y, z;
};


/* CLASS: NXSGOpenGLScale */
/**
 * Scenegraph scaling node
 *
 * @ingroup NanorexInterface, PluginArchitecture, GraphicsArchitecture
 */
class NXSGOpenGLScale : public NXSGOpenGLModelViewTransform {
public:
    NXSGOpenGLScale(double const& the_x,
                    double const& the_y,
                    double const& the_z) throw ()
        : x(the_x), y(the_y), z(the_z)  {}
    ~NXSGOpenGLScale() throw () {}
    bool apply(void) const throw ();
private:
    GLdouble x, y, z;
};


#if 0 // unused class - commented out
/* CLASS: NXSGOpenGLGenericTransform */
/**
 * Generic OpenGL transform
 *
 * @ingroup NanorexInterface, PluginArchitecture, GraphicsArchitecture
 */
class NXSGOpenGLGenericTransform : public NXSGOpenGLTransform {

public:
    NXSGOpenGLGenericTransform() throw () {}
    ~NXSGOpenGLGenericTransform() throw () {}

    bool apply(void) const throw();

private:
    GLdouble matrix[16];

    void zero() { for(int i=0; i<16; ++i) matrix[i] = 0.0; }
    void identity() { zero(); matrix[0] = matrix[5] = matrix[10] = matrix[15] =
1.0; }
};
#endif


/* CLASS NXSGOpenGLRenderable */
/*!
 *  Objects that can directly be drawn, as opposed to transforms
 *
 * @ingroup NanorexInterface, PluginArchitecture, GraphicsArchitecture
 */
class NXSGOpenGLRenderable : public NXSGOpenGLNode {
    
public:
    NXSGOpenGLRenderable() throw (NXException);
    
    ~NXSGOpenGLRenderable() throw (NXException);
    
    bool apply(void) const throw () {glCallList(display_list_id); return true;}
    
    /// Calls glNewList(). Call the plugin's render-method after this so that
    /// what the plugin draws using OpenGL becomes part of this display list
    bool beginRender(void) const throw ();
    
    /// Calls glEndList(). Call after the plugin does its OpenGL rendering.
    bool endRender(void) const throw ();
    
	void deleteRecursive(void) { }

#ifdef NX_DEBUG
    GLuint getDisplayListID(void) const { return display_list_id; }
#endif
    
protected:
    GLuint display_list_id;
};


class NXSGOpenGLMaterial : public NXSGOpenGLNode, public NXOpenGLMaterial {
public:
    NXSGOpenGLMaterial() throw () : NXSGOpenGLNode() ,NXOpenGLMaterial() {}
    NXSGOpenGLMaterial(NXOpenGLMaterial const& mat) throw()
        : NXSGOpenGLNode(), NXOpenGLMaterial(mat) {}
	~NXSGOpenGLMaterial() throw () {}
    /// Copy assignment from GL-material
    // NXSGOpenGLMaterial& operator = (NXOpenGLMaterial const& mat) throw ();
    bool apply(void) const throw ();

	void deleteRecursive(void) { }
};

} // Nanorex

#endif // NX_SCENEGRAPH_OPENGL_H
