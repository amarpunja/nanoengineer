// Copyright 2006 Nanorex, Inc.  See LICENSE file for details. 
// gcc -I/usr/include/python2.4 -c -Wall atombasehelp.c 

#include "Python.h"
#include "Numeric/arrayobject.h"

//#define DEBUG

#ifdef DEBUG
#define XX(z)   z
#define MARK()  printf("%s:%d\n", __FUNCTION__, __LINE__)
#define HEX(x)  printf("%s:%d %s=%p\n", __FUNCTION__, __LINE__, #x, x)
#define INT(x)  printf("%s:%d %s=%u\n", __FUNCTION__, __LINE__, #x, x)
#define DBL(x)  printf("%s:%d %s=%le\n", __FUNCTION__, __LINE__, #x, x)
#define STR(x)  printf("%s:%d %s\n", __FUNCTION__, __LINE__, x)
#else
#define XX(z)
#define MARK()
#define HEX(x)
#define INT(x)
#define DBL(x)
#define STR(x)
#endif

/*
 * There is a kind of polymorphism available with structs, as long as the
 * first few fields are identical. In this case, the only commonality is
 * the "key" field.
 */
/* the "base class" */
struct key_thing {
    int key;
    PyObject *self;
};

/*
 * Linked lists are used for bonds, and also to track which
 * sets this atom is a member of.
 */
struct pointerlist {
    int size;
    int arraysize;
    struct key_thing **lst;
};

struct xyz {
    double x, y, z;
};

struct atomstruct {
    int key;
    PyObject *self;
    int _eltnum, _atomtype;
    struct xyz _posn;
    struct pointerlist *sets;

    /* This stuff comes from sim/src/part.h. There are redundancies.
     * The information in _eltnum and _atomtype is probably equivalent
     * to the information in type and hybridization, but EricM has one
     * record-keeping scheme and Bruce has another.
     */
    /* struct atomType * */ void *type;
    /* enum hybridization */ int hybridization;
  
    struct atom **vdwBucket;
    struct atom *vdwPrev;
    struct atom *vdwNext;
    double inverseMass;
    
    // non-zero if this atom is in any ground jigs
    int isGrounded;
    
    int index;
    int atomID;
    int num_bonds;
    /* struct bond ** */ void *bonds;
};

struct bondstruct {
    int key;
    PyObject *self;
    unsigned int atomkey1, atomkey2;
    int v6;
    struct pointerlist *sets;
};

struct setstruct {
    int key;
    PyObject *self;
    struct pointerlist *members;
};

static void print_pointerlist(struct pointerlist *L)
{
    int i;
    printf("POINTERLIST %p <<\n", L);
    for (i = 0; i < L->size; i++)
	if (L->lst[i] == NULL) {
	    printf("Entry %d, entry is NULL\n", i);
	} else {
	    printf("Entry %d, entry = %p, key = %d\n",
		   i, L->lst[i], L->lst[i]->key);
	}
    printf(">> POINTERLIST\n");
}

static struct pointerlist *new_pointerlist(void)
{
    struct pointerlist *p = (struct pointerlist *) malloc(sizeof(struct pointerlist));
    p->size = 0;
    /* don't start out too big, we might have lots of these */
    p->arraysize = 20;
    p->lst = (struct key_thing **) malloc(p->arraysize * sizeof(struct key_thing *));
    return p;
}

static struct key_thing *has_key(struct pointerlist *n, unsigned int key)
{
    int i;
    for (i = 0; i < n->size; i++) {
	if (n->lst[i]->key == key)
	    return n->lst[i];
    }
    return NULL;
}

static PyObject *remove_from_pointerlist(struct pointerlist *head, unsigned int otherkey);

static PyObject * add_to_pointerlist(struct pointerlist *n, struct key_thing *other)
{
    HEX(n);
    HEX(other);
    INT(other->key);
    HEX(other->self);
    XX(print_pointerlist(n));
    if (n == NULL) {
	PyErr_SetString(PyExc_RuntimeError,
			"add_to_pointerlist: null list??");
	return NULL;
    }
    if (other == NULL) {
	PyErr_SetString(PyExc_RuntimeError,
			"add_to_pointerlist: second arg is NULL");
	return NULL;
    }
    if (other->key == 0) {
	printf("BADNESS: ");
	PyObject_Print(other->self, stdout, 0);
	printf("\n");

	PyErr_SetString(PyExc_RuntimeError,
			"add_to_pointerlist: key is zero");
	return NULL;
    }
    /* we already have somebody with the same key, so remove it */
    if (has_key(n, other->key) != NULL) {
	if (remove_from_pointerlist(n, other->key) == NULL)
	    return NULL;
    }
	n->size++;
    if (n->size > n->arraysize) {
	printf("GROW LIST FROM %d to %d\n", n->arraysize, 2 * n->arraysize);
	n->arraysize *= 2;
	n->lst = (struct key_thing **)
	    realloc(n->lst, n->arraysize * sizeof(struct key_thing *));
    }
	n->lst[n->size-1] = other;
	Py_INCREF(other->self);

    MARK();
    XX(print_pointerlist(n));
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *remove_from_pointerlist(struct pointerlist *head, unsigned int otherkey)
{
    int i;
    MARK();
    XX(printf("\n"));
    INT(otherkey);
    XX(print_pointerlist(head));
    if (head == NULL) {
	PyErr_SetString(PyExc_RuntimeError,
			"remove_from_pointerlist: empty list");
	return NULL;
    }
    MARK();
    /* find item to be removed, if it's here */
    for (i = 0; i < head->size; i++) {
	if (otherkey == head->lst[i]->key)
	    break;
    }
    MARK();
    if (i == head->size) {
	PyErr_SetString(PyExc_RuntimeError,
			"remove_from_pointerlist: no such entry");
	return NULL;
    }
    MARK();
    if (head->lst[i]->self == NULL) {
	PyErr_SetString(PyExc_RuntimeError,
			"remove_from_pointerlist: object to be removed is null");
	return NULL;
    }
    Py_DECREF(head->lst[i]->self);
    memmove(&head->lst[i], &head->lst[i+1],
	    (head->size - 1 - i) * sizeof(void*));
    head->size--;
    MARK();
    XX(print_pointerlist(head));
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *pointerlist_lookup(struct pointerlist *root, unsigned int key)
{
    struct key_thing *r = has_key(root, key);
    if (r == NULL) {
	PyErr_SetString(PyExc_KeyError,
			"pointerlist_lookup: no such key");
	return NULL;
    }
    Py_INCREF(r->self);
    return r->self;
}

/* -------------------------------------------------------------------- */

static unsigned int qsort_partition(struct key_thing **y, unsigned int f, unsigned int l)
{
    unsigned int up, down;
    struct key_thing *piv = y[f];
    up = f;
    down = l;
    do { 
        while (y[up]->key <= piv->key && up < l) {
            up++;
        }
        while (y[down]->key > piv->key) {
            down--;
        }
        if (up < down) {
	    struct key_thing *temp;
            temp = y[up];
            y[up] = y[down];
            y[down] = temp;
        }
    } while (down > up);
    y[f] = y[down];
    y[down] = piv;
    return down;
}

static void quicksort(struct key_thing **x, unsigned int first, unsigned int last)
{
    if (first < last) {
        unsigned int pivIndex = qsort_partition(x, first, last);
        if (pivIndex > 0)
	    quicksort(x, first, pivIndex-1);
	quicksort(x, pivIndex+1, last);
    }
}

static PyObject *extract_list(struct pointerlist *root, int values)
{
    PyObject *retval;
    int i;
    unsigned int *kdata;
    import_array();
    MARK();
    XX(print_pointerlist(root));
    if (root->size > 0) {
	quicksort(root->lst, 0, root->size-1);
    }
    MARK();
    if (values) {
	retval = PyList_New(0);
	for (i = 0; i < root->size; i++) {
	    PyList_Append(retval, root->lst[i]->self);
	    XX(PyObject_Print(root->lst[i]->self, stdout, 0));
	    XX(printf(" at address %p\n", root->lst[i]->self));
	}
	MARK();
	return retval;
    }
    retval = PyArray_FromDims(1, (int*)&(root->size), PyArray_INT);
    kdata = (unsigned int *) ((PyArrayObject*) retval)->data;
    for (i = 0; i < root->size; i++) {
	kdata[i] = root->lst[i]->key;
    }
    MARK();
    return PyArray_Return((PyArrayObject*) retval);
}

/* =============================================================== *
 *                                                                 *
 *                         OpenGL stuff                            *
 *                                                                 *
 * =============================================================== */

#ifdef MACOSX
#include <gl.h>
#include <glu.h>
#else
#ifdef _WIN32
#include <windows.h> /* Even MinGW includes this */
#endif
#include <GL/gl.h>
#include <GL/glu.h>
#endif

/* Font example from chapter 8 */

static GLubyte rasters[][13] = {
    {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0x18, 0x18, 0x00, 0x00, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18}, 
    {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x36, 0x36, 0x36, 0x36}, 
    {0x00, 0x00, 0x00, 0x66, 0x66, 0xff, 0x66, 0x66, 0xff, 0x66, 0x66, 0x00, 0x00}, 
    {0x00, 0x00, 0x18, 0x7e, 0xff, 0x1b, 0x1f, 0x7e, 0xf8, 0xd8, 0xff, 0x7e, 0x18}, 
    {0x00, 0x00, 0x0e, 0x1b, 0xdb, 0x6e, 0x30, 0x18, 0x0c, 0x76, 0xdb, 0xd8, 0x70}, 
    {0x00, 0x00, 0x7f, 0xc6, 0xcf, 0xd8, 0x70, 0x70, 0xd8, 0xcc, 0xcc, 0x6c, 0x38}, 
    {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x1c, 0x0c, 0x0e}, 
    {0x00, 0x00, 0x0c, 0x18, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x18, 0x0c}, 
    {0x00, 0x00, 0x30, 0x18, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0x18, 0x30}, 
    {0x00, 0x00, 0x00, 0x00, 0x99, 0x5a, 0x3c, 0xff, 0x3c, 0x5a, 0x99, 0x00, 0x00}, 
    {0x00, 0x00, 0x00, 0x18, 0x18, 0x18, 0xff, 0xff, 0x18, 0x18, 0x18, 0x00, 0x00}, 
    {0x00, 0x00, 0x30, 0x18, 0x1c, 0x1c, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0x00, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0x00, 0x38, 0x38, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x60, 0x60, 0x30, 0x30, 0x18, 0x18, 0x0c, 0x0c, 0x06, 0x06, 0x03, 0x03}, 
    {0x00, 0x00, 0x3c, 0x66, 0xc3, 0xe3, 0xf3, 0xdb, 0xcf, 0xc7, 0xc3, 0x66, 0x3c}, 
    {0x00, 0x00, 0x7e, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x78, 0x38, 0x18}, 
    {0x00, 0x00, 0xff, 0xc0, 0xc0, 0x60, 0x30, 0x18, 0x0c, 0x06, 0x03, 0xe7, 0x7e}, 
    {0x00, 0x00, 0x7e, 0xe7, 0x03, 0x03, 0x07, 0x7e, 0x07, 0x03, 0x03, 0xe7, 0x7e}, 
    {0x00, 0x00, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0xff, 0xcc, 0x6c, 0x3c, 0x1c, 0x0c}, 
    {0x00, 0x00, 0x7e, 0xe7, 0x03, 0x03, 0x07, 0xfe, 0xc0, 0xc0, 0xc0, 0xc0, 0xff}, 
    {0x00, 0x00, 0x7e, 0xe7, 0xc3, 0xc3, 0xc7, 0xfe, 0xc0, 0xc0, 0xc0, 0xe7, 0x7e}, 
    {0x00, 0x00, 0x30, 0x30, 0x30, 0x30, 0x18, 0x0c, 0x06, 0x03, 0x03, 0x03, 0xff}, 
    {0x00, 0x00, 0x7e, 0xe7, 0xc3, 0xc3, 0xe7, 0x7e, 0xe7, 0xc3, 0xc3, 0xe7, 0x7e}, 
    {0x00, 0x00, 0x7e, 0xe7, 0x03, 0x03, 0x03, 0x7f, 0xe7, 0xc3, 0xc3, 0xe7, 0x7e}, 
    {0x00, 0x00, 0x00, 0x38, 0x38, 0x00, 0x00, 0x38, 0x38, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0x30, 0x18, 0x1c, 0x1c, 0x00, 0x00, 0x1c, 0x1c, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0x06, 0x0c, 0x18, 0x30, 0x60, 0xc0, 0x60, 0x30, 0x18, 0x0c, 0x06}, 
    {0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0x00, 0xff, 0xff, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0x60, 0x30, 0x18, 0x0c, 0x06, 0x03, 0x06, 0x0c, 0x18, 0x30, 0x60}, 
    {0x00, 0x00, 0x18, 0x00, 0x00, 0x18, 0x18, 0x0c, 0x06, 0x03, 0xc3, 0xc3, 0x7e}, 
    {0x00, 0x00, 0x3f, 0x60, 0xcf, 0xdb, 0xd3, 0xdd, 0xc3, 0x7e, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0xc3, 0xc3, 0xc3, 0xc3, 0xff, 0xc3, 0xc3, 0xc3, 0x66, 0x3c, 0x18}, 
    {0x00, 0x00, 0xfe, 0xc7, 0xc3, 0xc3, 0xc7, 0xfe, 0xc7, 0xc3, 0xc3, 0xc7, 0xfe}, 
    {0x00, 0x00, 0x7e, 0xe7, 0xc0, 0xc0, 0xc0, 0xc0, 0xc0, 0xc0, 0xc0, 0xe7, 0x7e}, 
    {0x00, 0x00, 0xfc, 0xce, 0xc7, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3, 0xc7, 0xce, 0xfc}, 
    {0x00, 0x00, 0xff, 0xc0, 0xc0, 0xc0, 0xc0, 0xfc, 0xc0, 0xc0, 0xc0, 0xc0, 0xff}, 
    {0x00, 0x00, 0xc0, 0xc0, 0xc0, 0xc0, 0xc0, 0xc0, 0xfc, 0xc0, 0xc0, 0xc0, 0xff}, 
    {0x00, 0x00, 0x7e, 0xe7, 0xc3, 0xc3, 0xcf, 0xc0, 0xc0, 0xc0, 0xc0, 0xe7, 0x7e}, 
    {0x00, 0x00, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3, 0xff, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3}, 
    {0x00, 0x00, 0x7e, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x7e}, 
    {0x00, 0x00, 0x7c, 0xee, 0xc6, 0x06, 0x06, 0x06, 0x06, 0x06, 0x06, 0x06, 0x06}, 
    {0x00, 0x00, 0xc3, 0xc6, 0xcc, 0xd8, 0xf0, 0xe0, 0xf0, 0xd8, 0xcc, 0xc6, 0xc3}, 
    {0x00, 0x00, 0xff, 0xc0, 0xc0, 0xc0, 0xc0, 0xc0, 0xc0, 0xc0, 0xc0, 0xc0, 0xc0}, 
    {0x00, 0x00, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3, 0xdb, 0xff, 0xff, 0xe7, 0xc3}, 
    {0x00, 0x00, 0xc7, 0xc7, 0xcf, 0xcf, 0xdf, 0xdb, 0xfb, 0xf3, 0xf3, 0xe3, 0xe3}, 
    {0x00, 0x00, 0x7e, 0xe7, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3, 0xe7, 0x7e}, 
    {0x00, 0x00, 0xc0, 0xc0, 0xc0, 0xc0, 0xc0, 0xfe, 0xc7, 0xc3, 0xc3, 0xc7, 0xfe}, 
    {0x00, 0x00, 0x3f, 0x6e, 0xdf, 0xdb, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3, 0x66, 0x3c}, 
    {0x00, 0x00, 0xc3, 0xc6, 0xcc, 0xd8, 0xf0, 0xfe, 0xc7, 0xc3, 0xc3, 0xc7, 0xfe}, 
    {0x00, 0x00, 0x7e, 0xe7, 0x03, 0x03, 0x07, 0x7e, 0xe0, 0xc0, 0xc0, 0xe7, 0x7e}, 
    {0x00, 0x00, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0xff}, 
    {0x00, 0x00, 0x7e, 0xe7, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3}, 
    {0x00, 0x00, 0x18, 0x3c, 0x3c, 0x66, 0x66, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3}, 
    {0x00, 0x00, 0xc3, 0xe7, 0xff, 0xff, 0xdb, 0xdb, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3}, 
    {0x00, 0x00, 0xc3, 0x66, 0x66, 0x3c, 0x3c, 0x18, 0x3c, 0x3c, 0x66, 0x66, 0xc3}, 
    {0x00, 0x00, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x3c, 0x3c, 0x66, 0x66, 0xc3}, 
    {0x00, 0x00, 0xff, 0xc0, 0xc0, 0x60, 0x30, 0x7e, 0x0c, 0x06, 0x03, 0x03, 0xff}, 
    {0x00, 0x00, 0x3c, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x3c}, 
    {0x00, 0x03, 0x03, 0x06, 0x06, 0x0c, 0x0c, 0x18, 0x18, 0x30, 0x30, 0x60, 0x60}, 
    {0x00, 0x00, 0x3c, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0x3c}, 
    {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xc3, 0x66, 0x3c, 0x18}, 
    {0xff, 0xff, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x38, 0x30, 0x70}, 
    {0x00, 0x00, 0x7f, 0xc3, 0xc3, 0x7f, 0x03, 0xc3, 0x7e, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0xfe, 0xc3, 0xc3, 0xc3, 0xc3, 0xfe, 0xc0, 0xc0, 0xc0, 0xc0, 0xc0}, 
    {0x00, 0x00, 0x7e, 0xc3, 0xc0, 0xc0, 0xc0, 0xc3, 0x7e, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0x7f, 0xc3, 0xc3, 0xc3, 0xc3, 0x7f, 0x03, 0x03, 0x03, 0x03, 0x03}, 
    {0x00, 0x00, 0x7f, 0xc0, 0xc0, 0xfe, 0xc3, 0xc3, 0x7e, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0x30, 0x30, 0x30, 0x30, 0x30, 0xfc, 0x30, 0x30, 0x30, 0x33, 0x1e}, 
    {0x7e, 0xc3, 0x03, 0x03, 0x7f, 0xc3, 0xc3, 0xc3, 0x7e, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3, 0xc3, 0xfe, 0xc0, 0xc0, 0xc0, 0xc0}, 
    {0x00, 0x00, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x00, 0x00, 0x18, 0x00}, 
    {0x38, 0x6c, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0x00, 0x00, 0x0c, 0x00}, 
    {0x00, 0x00, 0xc6, 0xcc, 0xf8, 0xf0, 0xd8, 0xcc, 0xc6, 0xc0, 0xc0, 0xc0, 0xc0}, 
    {0x00, 0x00, 0x7e, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x78}, 
    {0x00, 0x00, 0xdb, 0xdb, 0xdb, 0xdb, 0xdb, 0xdb, 0xfe, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0xfc, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0x7c, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0x7c, 0x00, 0x00, 0x00, 0x00}, 
    {0xc0, 0xc0, 0xc0, 0xfe, 0xc3, 0xc3, 0xc3, 0xc3, 0xfe, 0x00, 0x00, 0x00, 0x00}, 
    {0x03, 0x03, 0x03, 0x7f, 0xc3, 0xc3, 0xc3, 0xc3, 0x7f, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0xc0, 0xc0, 0xc0, 0xc0, 0xc0, 0xe0, 0xfe, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0xfe, 0x03, 0x03, 0x7e, 0xc0, 0xc0, 0x7f, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0x1c, 0x36, 0x30, 0x30, 0x30, 0x30, 0xfc, 0x30, 0x30, 0x30, 0x00}, 
    {0x00, 0x00, 0x7e, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0x18, 0x3c, 0x3c, 0x66, 0x66, 0xc3, 0xc3, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0xc3, 0xe7, 0xff, 0xdb, 0xc3, 0xc3, 0xc3, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0xc3, 0x66, 0x3c, 0x18, 0x3c, 0x66, 0xc3, 0x00, 0x00, 0x00, 0x00}, 
    {0xc0, 0x60, 0x60, 0x30, 0x18, 0x3c, 0x66, 0x66, 0xc3, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0xff, 0x60, 0x30, 0x18, 0x0c, 0x06, 0xff, 0x00, 0x00, 0x00, 0x00}, 
    {0x00, 0x00, 0x0f, 0x18, 0x18, 0x18, 0x38, 0xf0, 0x38, 0x18, 0x18, 0x18, 0x0f}, 
    {0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18}, 
    {0x00, 0x00, 0xf0, 0x18, 0x18, 0x18, 0x1c, 0x0f, 0x1c, 0x18, 0x18, 0x18, 0xf0}, 
    {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x06, 0x8f, 0xf1, 0x60, 0x00, 0x00, 0x00} 
};

static int _init_bitmap_font(void)
{
    GLuint fontOffset;
    GLuint i;
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
    fontOffset = glGenLists(128);
    for (i = 32; i < 127; i++) {
        glNewList(i + fontOffset, GL_COMPILE);
	glBitmap(8, 13, 0.0, 2.0, 10.0, 0.0, rasters[i - 32]);
        glEndList();
    }
    return fontOffset;
}



/*
 * Local Variables:
 * c-basic-offset: 4
 * tab-width: 8
 * End:
 */
