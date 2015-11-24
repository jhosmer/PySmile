/*
 *  pysmile.c
 *  PySmile
 *
 *  Author: Jonathan Hosmer
 *  Date: 11/23/15
 *
 *  Copyright 2015-2016 Jonathan Hosmer
 */

#include "pysmile.h"
#include "smile.h"

static struct module_state _state;

#define BUFFER_SIZE 65536

/*
static PyObject * pysmile_encode(PyObject *self, PyObject *args) {
    PyObject *jsonModule = PyImport_Import(PyBytes_FromString("json"));
    PyObject *encodeFunc = PyObject_GetAttrString(jsonModule, "dumps");
    PyObject* result = PyObject_CallObject(encodeFunc, args);
    if (result == NULL) {
        Py_RETURN_NONE;
    }
    return result;
}

PyDoc_STRVAR(pysmile_encode__doc__,
             "Encode an object to SMILE format data.\n"
             "\n"
             " - parameters - \n"
             "obj - The object to be encoded.\n");
*/

static PyObject * pysmile_decode(PyObject *self, PyObject *args) {
    char * str;
    int str_len;
    if (!PyArg_ParseTuple(args, "s#", &str, &str_len))
        return NULL;
    char dst[BUFFER_SIZE] = {'\0'};
    PyObject *result;
    smile_decode_block_reset();
    ssize_t bytes_decoded = smile_decode_block(dst, BUFFER_SIZE, str, str_len);
    if (PyObject_IsInstance(args, (PyObject *)&PyUnicode_Type)) {
        // Convert to wide characters
        wchar_t bytes_out[BUFFER_SIZE] = {'\0'};
        mbstowcs(bytes_out, dst, bytes_decoded);
        result = PyUnicode_FromWideChar(bytes_out, bytes_decoded);
    } else {
        result = PyString_FromString(dst);
    }
    if (result == NULL) {
        Py_RETURN_NONE;
    }
    return result;
}

PyDoc_STRVAR(pysmile_decode__doc__,
             "Decode SMILE format data into a JSON string.\n"
             "\n"
             " - parameters - \n"
             "obj - The object/string/bytes to be decoded.\n");

static PyMethodDef pysmileMethods[] = {
    {"decode",  (PyCFunction)pysmile_decode,    METH_VARARGS,   pysmile_decode__doc__},
    // {"encode",  (PyCFunction)pysmile_encode,    METH_VARARGS,   pysmile_encode__doc__},
    {NULL,      NULL,                           0,              NULL},
};

PyDoc_STRVAR(pysmile_module_documentation,
             "Python SMILE format encode/decode.\n"
             "\n"
             "decode(obj) -- Decode SMILE format binary data into a JSON string.\n"
             "encode(obj) -- Encode an object into SMILE binary data format.\n"
             "\n");

void initpysmile(void) {
    PyObject *module;
    module = Py_InitModule3("pysmile", pysmileMethods, pysmile_module_documentation);
    if (module == NULL)
        return;

    struct module_state *st = GETSTATE(module);
    st->error = PyErr_NewException("pysmile.error", NULL, NULL);
    if (st->error == NULL) {
        Py_DECREF(module);
        return;
    }
    smile_decode_block_init();
}
