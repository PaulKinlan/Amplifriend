function RenderItemTemplate($f, item) {

    if ($f == null) {
        return;
    }
    
    var Id = replaceAll($f.html(), "${Id}", item.Id);
    var FirefoxId = replaceAll(Id, "$%7BId%7D", item.Id);

    var Title = replaceAll(FirefoxId, "${Title}", item.Title);
    var FirefoxTitle = replaceAll(Title, "$%7BTitle%7D", item.Title);

    var Description = replaceAll(FirefoxTitle, "${Description}", item.Description);
    var FirefoxDescription = replaceAll(Description, "$%7BDescription%7D", item.Description);

    var PublishDate = replaceAll(FirefoxDescription, "${PublishDate}", item.Date);
    var FirefoxPublishDate = replaceAll(PublishDate, "$%7BPublishDate%7D", item.Date);

    var PrettyDate = replaceAll(FirefoxPublishDate, "${PrettyDate}", item.PrettyDate);
    var FirefoxPrettyDate = replaceAll(PrettyDate, "$%7BPrettyDate%7D}", item.PrettyDate);

    var ItemContent = replaceAll(FirefoxPrettyDate, "${ItemContentPreview}", item.ItemContentPreview);
    var FirefoxItemContent = replaceAll(ItemContent, "$%7BItemContentPreview%7D", item.ItemContentPreview);

    var SourceLink = replaceAll(FirefoxItemContent, "${SourceLink}", item.SourceLink);
    var FirefoxSourceLink = replaceAll(SourceLink, "$%7BSourceLink%7D", item.SourceLink);

    var Data = replaceAll(FirefoxSourceLink, "${Data}", item.Data);
    var FirefoxData = replaceAll(Data, "$%7BData%7D", item.Data);

    var SourceId = replaceAll(FirefoxData, "${SourceId}", item.SourceId);
    var FirefoxSourceId = replaceAll(SourceId, "$%7BSourceId%7D", item.SourceId);

    var CommentCount = replaceAll(FirefoxSourceId, "${CommentCount}", item.CommentCount);
    var FirefoxCommentCount = replaceAll(CommentCount, "$%7BCommentCount%7D", item.CommentCount);

    var SourceTypeName = replaceAll(FirefoxCommentCount, "${SourceTypeName}", item.SourceTypeName);
    var FirefoxSourceTypeName = replaceAll(SourceTypeName, "$%7BSourceTypeName%7D", item.SourceTypeName);

    var SourceTitle = replaceAll(FirefoxSourceTypeName, "${SourceTitle}", item.SourceTitle);
    var FirefoxSourceTitle = replaceAll(SourceTitle, "$%7BSourceTitle%7D", item.SourceTitle);

    return FirefoxSourceTitle;
}

function replaceAll(OldString, FindString, ReplaceString) {

    var SearchIndex = 0;

    var NewString = "";
    
    while (OldString.indexOf(FindString, SearchIndex) != -1) {
        NewString += OldString.substring(SearchIndex, OldString.indexOf(FindString, SearchIndex));
        NewString += ReplaceString;
        SearchIndex = (OldString.indexOf(FindString, SearchIndex) + FindString.length);
    }
    NewString += OldString.substring(SearchIndex, OldString.length);
    return NewString;
}

encodeHTML = function(original) {
    return EscapeHTML(original).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
};

encodeHTMLWhiteList = function(original) {
    return original.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace('\n','<br/>');
};

decodeHTML = function(original) {
    return original.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
};

RenderButtonRollovers = function() {

    $(".ro").mouseover(
        function() {
            if ($(this).attr("src").indexOf("_active") == -1) {
                var newSrc = $(this).attr("src").replace("_up.png", "_active.png");
                $(this).attr("src", newSrc);
            }
            
        }
    )

        $(".ro").mouseout(
        function() {
            if ($(this).attr("src").indexOf("_active") != -1) {
                var newSrc = $(this).attr("src").replace("_active.png", "_up.png");
                $(this).attr("src", newSrc);
            }

        }
    )


    }

EscapeHTML = function(original) {
    var eHtml = escape(original);
    eHtml = eHtml.replace(/\//g, "%2F");
    eHtml = eHtml.replace(/\?/g, "%3F");
    eHtml = eHtml.replace(/=/g, "%3D");
    eHtml = eHtml.replace(/&/g, "%26");
    eHtml = eHtml.replace(/@/g, "%40");
    return eHtml;
}

AjaxFailure = function(XMLHttpRequest, textStatus, errorThrown) {
	debugger
    if (textStatus == "timeout") {
        alert("Sorry, there was a delay in accessing the site database and the request has timed out. The site may be busy or having problems. If this problem persists, please contact the site administrator.");
    }
    else {
        alert("Sorry, there was an error and the request could not be completed. The site may be busy or having problems. If this problem persists, please contact the site administrator.");
    }
};
