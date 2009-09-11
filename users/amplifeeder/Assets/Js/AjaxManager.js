function AjaxManager(parameterObject, serviceMethodName, successCallback, errorCallBack) {
    $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        timeout:25000,
        url: serviceMethodName,
        data: parameterObject,
        success: function(msg) { successCallback(msg) },
        error: function(XMLHttpRequest, textStatus, errorThrown) { errorCallBack(XMLHttpRequest, textStatus, errorThrown) }
    });
}
