$(document).ready(function() { $("body").hide(); LoadTemplate(); });

LoadTemplate = function() {
    $("#TemplateDump").load("/{{user.username}}/Themes/" + ThemeName + "/" + ThemeName + ".detail.template.html", function() { TemplateLoaded() }).hide();
}

TemplateLoaded = function() {
    $('#Stylesheet').attr('href', "/{{user.username}}/Themes/" + ThemeName + "/" + ThemeName + ".template.css");
    $("#TemplateDump").find("#DetailTemplate").appendTo("#TemplateHolder");
    LoadItem();
}

LoadItem = function() {

    $("#alertbox").hide();
    var itemID = getQuerystring("id");

    var parameterObject = '{"itemID":"' + itemID + '", "numberToReturn":"' + '10' + '"}';
    AjaxManager(parameterObject, "/{{user.username}}/UIService.asmx/GetDetailItem", ItemLoaded, AjaxFailure);    
}

ItemLoaded = function(data) {
	var item =  data.d

    $template = $("#TemplateDump").find("." + item.Item.SourceTypeName);

    $("#TemplateItemHolder").append(RenderItemTemplate($template, item.Item));
    RenderChannelItems(item.FeedItems);
    RenderCommentForm(item.Comments);

    if (item.Settings.Title.length == 0) {
        $("#title").hide();
        document.title = "AmpliFeeder";
    }
    else {
        $("#title").html('<a href="default.aspx">' + item.Settings.Title + '</a>');
        document.title = item.Settings.Title;
    }

    if (item.Settings.Tagline.length == 0) {
        $("#tagline").hide();
    }
    else {
        $("#tagline").html(item.Settings.Tagline);
    }

    if (item.Settings.About.length == 0) {
        $("#about").hide();
    }
    else {
        $("#about").html(item.Settings.About);
    }

    if (typeof DetailPageRendered == 'function') {
        DetailPageRendered();
    } 
}

RenderCommentForm = function(data) {

    //var items = eval('(' + data.d + ')');
    $.each(data, function(i, item) { BuildComment(item); });
    var $name = $('<h5>Leave a Comment</h5><label for="txtName">Name</label><br/><input class="formstyle" id="txtName" type="text" /><br/>');
    var $email = $('<label for="txtEmail">Email</label><br/><input class="formstyle" id="txtEmail" type="text" /><br/>');
    var $comment = $('<label for="txtComment">Comment</label><br/><textarea rows="10" class="formstyle" id="txtComment" /><br/><br/>');

    var $btn = $('<img src="/Assets/img/buttons/submitbutton_up.png" alt="submit" />');
    $btn.click(function() { ValidateComment() }).mouseover(function() { document.body.style.cursor = "pointer" }).mouseout(function() { document.body.style.cursor = "auto" });
    $("#CommentFormHolder").append($name).append($email).append($comment).append($btn);
    $(".validator").hide();

    $("body").show();
}

ValidateComment = function() {

    var errorMessage = "";
    var ok = true;
    $("#alertbox").empty();

    var fromname = $("#txtName").val();
    var message = $("#txtComment").val();
    var email = $("#txtEmail").val();

    if (fromname == "") {
        ok = false;
        errorMessage = errorMessage + "Name is a required field<br/>";
    }

    if (message == "") {
        ok = false;
        errorMessage = errorMessage + "Comment is a required field<br/>";
    }

    if (email == "") {
        ok = false;
        errorMessage = errorMessage + "Email is a required field<br/>";
    }

    if (!isValidEmail(email)) {
        ok = false;
        errorMessage = errorMessage + "Email is not valid<br/>";
    }

    if (!ok) {

        $("#alertbox").html(errorMessage).show();
        return;
    }

    SubmitComment();
}

SubmitComment = function() {

    var itemID = getQuerystring("id");
    var fromname = encodeHTMLWhiteList($("#txtName").val());
    var message = encodeHTMLWhiteList($("#txtComment").val());
    var email = encodeHTMLWhiteList($("#txtEmail").val());

    var parameterObject = '{"itemID":"' + itemID + '", "name":"' + fromname + '", "message":"' + message + '", "email":"' + email + '"}';
    AjaxManager(parameterObject, "UIService.asmx/SubmitComment", CommentSubmitted, AjaxFailure);
}

CommentSubmitted = function(data) {

    $("#alertbox").html("Thanks. Your comment is currently awaiting moderation.").show();
}

getQuerystring = function(key, default_) {

    if (default_ == null) default_ = "";
    key = key.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regex = new RegExp("[\\?&]" + key + "=([^&#]*)");
    var qs = regex.exec(window.location.href);
    if (qs == null)
        return default_;
    else
        return qs[1];
}

isValidEmail = function(strEmail) {

    validRegExp = /^[^@]+@[^@]+.[a-z]{2,}$/i;

    if (strEmail.search(validRegExp) == -1) {
        return false;
    }
    return true;
}

BuildComment = function(item) {

    $comment = $('<div class="commentname">' + item.Name + ' says</div><div class="commentdate">' + item.Date + '</div><div class="commentbody">' + item.CommentBody + '</div>');
    
    $("#CommentHolder").append($comment);
}

RenderChannelItems = function(data) {

    var $items = "";
    $.each(data, function(i, item) { $items = $items + RenderChannelItem(item); });
    $("#ChannelItems").append("<ul id='channelitems'>" + $items + "</ul>");
}

RenderChannelItem = function(item) {

    return ("<li><img src='/{{user.username}}/Assets/img/icons/24/" + item.SourceTypeName + ".png' /><a href='/{{user.username}}/detail.aspx?id=" + item.Id + "'>" + item.Title + "</a></li>");
}

