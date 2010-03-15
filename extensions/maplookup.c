#include <Python.h>
#include <stdio.h>
#include <inttypes.h>

char * __revision__ = "$Id: maplookup.c,v 1.12 2005-06-29 06:49:12 alf Exp $";


/* PYTHON EQUIVALENCES
   # def _has_couple(couple, mapping): 
   #     for a,b in mapping:
   #         if b is couple[1] and a is couple[0]: 
   #             return TRUE 
   #     return FALSE 

   # def _partner(index, node, mapping): 
   #     for i in mapping:
   #         if i[index] is node: 
   #             return i[1-index]
   #     return None

   #    def fmes_node_equal(self, n1, n2):
   #        """ function to compare subtree during mapping """
   #        hk1, hk2 = self._d1.has_key, self._d2.has_key
   #        mapping = self._mapping
   #        # factor 2.5 for tree expansion compensation
   #        length = 0
   #        i = 0
   #        for a,b in mapping:
   #            i += 1
   #            if hk1((id(n1), id(a))):
   #                if hk2((id(n2), id(b))):
   #                       length += 1
   ##         length = len([a for a,b in mapping
   ##                       if hk1((id(n1), id(a))) and hk2((id(n2), id(b)))])
   #        fact = 2.5*length/float(max(n1[N_ISSUE], n2[N_ISSUE]))
   #        if fact >= self.T:
   #            return TRUE
   #        return FALSE
*/


/******************* functions specific to the fmes algorithm *****************/
static short N_ISSUE = 5 ;

/* function to init objects for the next functions
 *
 * arguments are (*mapping, *cache_dict1, *cache_dict2, T)
 */
static PyObject *_mapping, *_dict1, *_dict2 ;
static double _T_treshold ;

static void free_dicts(void) 
{
	Py_XDECREF(_dict1) ;
	_dict1 = NULL ;
	Py_XDECREF(_dict2) ;
	_dict2 = NULL ;
}

static void free_global(void) 
{
	Py_XDECREF(_mapping) ;
	_mapping = NULL ;
	free_dicts() ;
}


static PyObject *fmes_init(PyObject *self, PyObject *args)
{
	free_global() ;
	if (!PyArg_ParseTuple(args, "OOOd", &_mapping, &_dict1, &_dict2, &_T_treshold))
		return NULL ;
	Py_INCREF(_mapping) ;
	Py_INCREF(_dict1) ;
	Py_INCREF(_dict2) ;
	Py_INCREF(Py_None) ;
	return Py_None ;
}

static PyObject *fmes_end(PyObject *self, PyObject *args)
{
	free_global() ;
	Py_INCREF(Py_None) ;
	return Py_None ;
}

static PyObject *match_end(PyObject *self, PyObject *args)
{
	free_dicts() ;
	Py_INCREF(Py_None) ;
	return Py_None ;
}


/* look in mapping's couples for an occurence of couple 
 * return 1 if found, None either
 */
static PyObject *has_couple(PyObject *self, PyObject *args)
{
	PyObject *object1, *object2, *couple;
	int i;
	if (!PyArg_ParseTuple(args, "OO", &object1, &object2))
		return NULL;
	for (i=0; i<PyList_GET_SIZE(_mapping); i++) 
	{
		couple = PyList_GET_ITEM(_mapping, i);
		if (object1 == PyTuple_GET_ITEM(couple, 0) && 
		    object2 == PyTuple_GET_ITEM(couple, 1))
			return Py_BuildValue("i", 1);
	}
	Py_INCREF(Py_None);
	return Py_None;
}


/* look in mapping's couples for an occurence of node at index position
 * (index = 0 or 1)
 * return node's partner if found, None either
 */
static PyObject *partner(PyObject *self, PyObject *args)
{
	PyObject *node, *couple;
	int index, i;
	if (!PyArg_ParseTuple(args, "iO", &index, &node))
		return NULL;
	for (i=0; i<PyList_GET_SIZE(_mapping); i++) 
	{
		couple = PyList_GET_ITEM(_mapping, i);
		if (node == PyTuple_GET_ITEM(couple, index)) 
			return Py_BuildValue("O", PyTuple_GET_ITEM(couple, 1-index));
	}
	Py_INCREF(Py_None);
	return Py_None;
}

/* function to compare subtree during fmes mapping
 *
 */
static PyObject *fmes_node_equal(PyObject *self, PyObject *args)
{
	PyObject *node1, *node2, *couple ;
	long max_issue, node2_issue ;
	double factor ;
	int seq_num = 0, i ;
  
	if ((_mapping == NULL) || (_dict1 == NULL) || (_dict2 == NULL))
	{
		PyErr_SetString( PyExc_RuntimeError, "you must call fmes_init first" );
		return NULL ;
	}
	if (!PyArg_ParseTuple(args, "OO", &node1, &node2))
	{
		return NULL;
	}
	for (i=0; i<PyList_GET_SIZE(_mapping); i++) 
	{
		PyObject *key ;
		couple = PyList_GET_ITEM(_mapping, i) ;
		key = PyTuple_New(2);
		Py_INCREF(key);
		PyTuple_SET_ITEM(key, 0, PyLong_FromVoidPtr(node1));
		PyTuple_SET_ITEM(key, 1, PyLong_FromVoidPtr(PyTuple_GET_ITEM(couple, 0)));
		if (PyDict_GetItem(_dict1, key) != NULL)
		{
			Py_DECREF(key) ;
			key = PyTuple_New(2);
			Py_INCREF(key);
			PyTuple_SET_ITEM(key, 0, PyLong_FromVoidPtr(node2));
			PyTuple_SET_ITEM(key, 1, PyLong_FromVoidPtr(PyTuple_GET_ITEM(couple, 1)));
			if (PyDict_GetItem(_dict2, key) != NULL)
			{
				seq_num += 1 ;
			}
			Py_DECREF(key) ;
		}
		else  
		{
			Py_DECREF(key) ;
		}
	}

	max_issue = PyInt_AS_LONG(PyList_GET_ITEM(node1, N_ISSUE)) ;
	node2_issue = PyInt_AS_LONG(PyList_GET_ITEM(node2, N_ISSUE)) ;
	if (max_issue < node2_issue) 
		max_issue = node2_issue ;
    
	factor = 2.5 * seq_num / max_issue ;
	if (factor >= _T_treshold) 
	{
		return Py_BuildValue("i", 1) ;
	}
	else
	{
		Py_INCREF(Py_None);
		return Py_None;
	}
}


static int is_equal( PyObject* equal, PyObject* X, int x, PyObject* Y, int y )
{
        PyObject *ob1, *ob2, *args, *res;
        ob1 = PySequence_GetItem( X, x );
        ob2 = PySequence_GetItem( Y, y );
        args = Py_BuildValue( "NN", ob1, ob2 );
        res = PyObject_CallObject( equal, args );
        Py_DECREF( args );
        return PyObject_IsTrue( res );
}

static int get_v( int* V, int d, int k )
{
        /* accessor function for V[d][K] which is stored as a triangle matrix */
        return V[d+k+1];
}

static void set_v( int* V, int d, int k, int v )
{
        /* accessor function for V[d][K] which is stored as a triangle matrix */
        V[d+k+1] = v;
}

static PyObject* lcs2( PyObject* self, PyObject* args )
{
        PyObject *X, *Y, *equal, *result, *ox, *oy;
        int N, M, max, D, k, x, y, nmax;
        int **V, *res, *resp;
        int xs, idx, v_up, v_down;
        
        if (!PyArg_ParseTuple( args, "OOO", &X,&Y,&equal ))
                return NULL;
        if (!PySequence_Check(X) || !PySequence_Check(Y)) {
                PyErr_SetString( PyExc_TypeError, "First two args must be sequences" );
                return NULL;
        }
        N = PySequence_Length(X);
        M = PySequence_Length(Y);
        max = N + M;
        V = (int**)malloc( (2*max+1)*sizeof(int*) );
        memset( V, 0, (2*max+1)*sizeof(int*)  );
        V[0] = (int*)malloc( 3*sizeof(int) );
        memset( V[0], 0, 3*sizeof(int) );
        nmax = (N>M ? N : M );
        res = (int*)malloc( nmax*sizeof(int)*2 );
        
        for(D=0;D<=max;++D) {
                V[D+1] = (int*)malloc( (2*D+5)*sizeof(int) );
                memset( V[D+1], 0, (2*D+5)*sizeof(int) );
                for(k=-D;k<=D;k+=2) {
                        v_up = get_v( V[D], D, k+1 );
                        v_down = get_v( V[D], D, k-1 ); 
                        if ( k==-D || ( k != D && v_down < v_up) ) {
                                x = v_up;
                        } else {
                                x = v_down + 1;
                        }
                        y = x - k;
                        while ( x < N && y < M && is_equal( equal, X, x, Y, y ) ) {
                                x += 1;
                                y += 1;
                                /*common = 0;*/
                        }
                        set_v(V[D+1],D+1,k,x);
                        if ( x >= N && y >= M ) {
                                /* build the maximal path */
                                k = N-M;
                                resp = res;
                                x = N;
                                y = M;
                                while(D>=0) {
                                        v_up = get_v( V[D], D, k+1 );
                                        v_down = get_v( V[D], D, k-1 ); 
                                        if ( k==-D || ( k != D && v_down < v_up) ) {
                                                xs = v_up;
                                                k = k + 1;
                                        } else {
                                                xs = v_down + 1;
                                                k = k - 1;
                                        }
                                        while( x>xs )
                                        {
                                                *resp++ = --x;
                                                *resp++ = --y;
                                        }
                                        x = get_v(V[D],D,k);
                                        y = x - k;
                                        D -= 1;         
                                }
                                /* now builds the python list from res */
                                result = PyList_New( (resp-res)/2 );
                                idx = 0;
                                resp-=2;
                                while(resp>=res) {
                                        ox = PySequence_GetItem( X, resp[0] );
                                        oy = PySequence_GetItem( Y, resp[1] );
                                        PyList_SetItem( result, idx, Py_BuildValue("NN",ox,oy) );
                                        resp-=2;
                                        idx+=1;
                                }
                                for(idx=0;idx<D;++idx) {
                                        if (V[idx])
                                                free(V[idx]);
                                        else
                                                break;
                                }
                                free(V);               
                                free(res);
                                return result;
                        }
                }
        }
        for(idx=0;idx<D;++idx) {
                if (V[idx])
                        free(V[idx]);
                else
                        break;
        }
        free(V);               
        free(res);
        Py_INCREF(Py_None);
        return Py_None;
}


/***** PYTHON INITIALISATION *****/
static PyMethodDef MAPLOOKUP_METHODS[] = {
	{"has_couple", has_couple, METH_VARARGS},
	{"partner", partner, METH_VARARGS},
	{"fmes_init", fmes_init, METH_VARARGS},
	{"fmes_end", fmes_end, METH_VARARGS},
	{"match_end", match_end, METH_VARARGS},
	{"fmes_node_equal", fmes_node_equal, METH_VARARGS},
	{"lcs2", lcs2, METH_VARARGS},
	{NULL,   NULL}        /* Sentinel */
};


void initmaplookup(void)
{
	(void) Py_InitModule("maplookup", MAPLOOKUP_METHODS);
}

