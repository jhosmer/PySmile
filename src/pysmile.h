/*
 *  pysmile.h
 *  PySmile
 *
 *  Author: Jonathan Hosmer
 *  Date: 11/23/15
 *
 *  Copyright 2015-2016 Jonathan Hosmer
 */

#ifndef pysmile_h
#define pysmile_h

#include "Python.h"

void initpysmile(void);

struct module_state {
    PyObject *error;
};

#define GETSTATE(m) (&_state)

#endif /* defined(pysmile_h) */
