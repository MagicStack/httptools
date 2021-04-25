use cpython::{py_class, py_fn, py_module_initializer, PythonObject};
use cpython::{PyErr, PyResult, Python, ToPyObject, PyBytes, PyObject, PyString};
use cpython::exc::NotImplementedError;
use http::Uri;
use bytes::Bytes;

py_module_initializer!(url_parser, |py, m| {
    m.add(py, "__doc__", "This module is implemented in Rust.")?;
    m.add(py, "__all__", ("parse_url",).to_py_object(py))?;
    m.add(py, "URL", py.get_type::<URL>())?;
    m.add(py, "parse_url", py_fn!(py, parse_url(url: &[u8])))?;
    Ok(())
});

py_class!(pub class URL |py| {
    data uri: Uri;

    @property def schema(&self) -> PyResult<PyObject> {
        match self.uri(py).scheme_str() {
            Some(scheme) => Ok(PyBytes::new(py, scheme.as_bytes()).into_object()),
            None => Ok(py.None()),
        }
    }

    @property def host(&self) -> PyResult<PyObject> {
        match self.uri(py).host() {
            Some(host) => Ok(PyBytes::new(py, host.as_bytes()).into_object()),
            None => Ok(py.None()),
        }
    }

    @property def port(&self) -> PyResult<PyObject> {
        match self.uri(py).port_u16() {
            Some(port) => Ok(port.to_py_object(py).into_object()),
            None => Ok(py.None()),
        }
    }

    @property def path(&self) -> PyResult<PyString> {
        Ok(self.uri(py).path().to_py_object(py))
    }

    @property def query(&self) -> PyResult<PyObject> {
        match self.uri(py).query() {
            Some(query) => Ok(PyBytes::new(py, query.as_bytes()).into_object()),
            None => Ok(py.None()),
        }
    }

    @property def fragment(&self) -> PyResult<PyObject> {
        Err(PyErr::new::<NotImplementedError, _>(py, "fragment is not implemented"))
    }

    @property def userinfo(&self) -> PyResult<PyObject> {
        Err(PyErr::new::<NotImplementedError, _>(py, "userinfo is not implemented"))
    }
});

fn get_invalid_url_error(py: Python, message: String) -> PyResult<PyErr> {
    let errors = py.import("httptools.parser.errors")?;
    let url_error = errors.get(py, "HttpParserInvalidURLError")?.extract(py)?;
    Ok(PyErr::new_lazy_init(
        url_error,
        Some(message.to_py_object(py).into_object())
    ))
}

fn parse_url(py: Python, url: &[u8]) -> PyResult<URL> {
    match Uri::from_shared(Bytes::from(url)) {
        Ok(uri) => URL::create_instance(py, uri),
        Err(e) => Err(get_invalid_url_error(py, e.to_string())?)
    }
}
