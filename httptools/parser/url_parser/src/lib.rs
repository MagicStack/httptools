use cpython::{py_class, py_fn, py_module_initializer, PythonObject};
use cpython::{PyErr, PyResult, Python, ToPyObject, PyBytes, PyObject};
use url::Url;
use std::str::from_utf8;

py_module_initializer!(url_parser, |py, m| {
    m.add(py, "__doc__", "This module is implemented in Rust.")?;
    m.add(py, "__all__", ("parse_url",).to_py_object(py))?;
    m.add(py, "URL", py.get_type::<URL>())?;
    m.add(py, "parse_url", py_fn!(py, parse_url(url: &[u8])))?;
    Ok(())
});

py_class!(pub class URL |py| {
    data _url: Url;

    @property def schema(&self) -> PyResult<PyBytes> {
        Ok(PyBytes::new(py, self._url(py).scheme().as_bytes()))
    }

    @property def host(&self) -> PyResult<PyObject> {
        match self._url(py).host_str() {
            Some(host_str) => Ok(PyBytes::new(py, host_str.as_bytes()).into_object()),
            None => Ok(py.None()),
        }
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
    match from_utf8(url) {
        Ok(url_str) => match Url::parse(url_str) {
            Ok(parsed_url) => URL::create_instance(
                py,
                parsed_url,
            ),
            Err(e) => Err(get_invalid_url_error(py, e.to_string())?)
        },
        Err(e) => Err(get_invalid_url_error(py, e.to_string())?)
    }
}
