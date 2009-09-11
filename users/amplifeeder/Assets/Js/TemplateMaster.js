/// <reference path="jquery.intellisense.js"/>
/// <reference path="AjaxManager.js"/>

var PageSize;
var PageCount;
var PageNumber = 1;
var ItemFilterType = "None";
var ItemFilterArgument = "None";
var TagPage = 1;
var init = true;

$(document).ready(function() { $("body").hide(); LoadTemplate(); });

LoadTemplate = function() {
	$("#TemplateDump").load("/{{user.username}}/Themes/" + ThemeName + "/" + ThemeName + ".template.html", function() { TemplateLoaded(); }).hide();
};

TemplateLoaded = function() {
    $('#Stylesheet').attr('href', "/{{user.username}}/Themes/" + ThemeName + "/" + ThemeName + ".template.css");
    $("#TemplateDump").find("#MasterTemplate").appendTo("#TemplateHolder");
    PageSize = $("#PageSize").text();
    LoadAndRenderTags();
    LoadAndRenderChannels();
    LoadAndRenderFeatures();
    RenderItemTypes();
    $("#alertbox").mouseover(function() { document.body.style.cursor = "pointer"; }).mouseout(function() { document.body.style.cursor = "auto"; }).hide().click(function() { ChannelResetClick(); });
    InitializeSearch();

    LoadAndRenderFeedItemPackage();
    $.browser.mozilla ? $("body").keypress(checkForEnter) : $("body").keydown(checkForEnter);
};

PagerClick = function(pageclickednumber) {
    PageNumber = pageclickednumber;
    LoadAndRenderFeedItemPackage();
}

LoadAndRenderFeedItemPackage = function() {

        var parameterObject = '{"PageSize":"' + PageSize + '", "PageNumber":"' + PageNumber + '", "ItemFilterType":"' + ItemFilterType + '", "ItemFilterArgument":"' + ItemFilterArgument + '"}';

        var method;
		{% if cname %}
		init ? method = "/{{user.username}}/UIService.asmx/GetInitItemsPackage" : method = "/{{user.username}}/UIService.asmx/GetItemsPackage";
        {% else %}
		init ? method = "/{{user.username}}/UIService.asmx/GetInitItemsPackage" : method = "/{{user.username}}/UIService.asmx/GetItemsPackage";
		{% endif %}
        AjaxManager(parameterObject, method, ProcessFeedItemPackage, AjaxFailure);
};

ProcessFeedItemPackage = function(data) {

    $("#TemplateItemsHolder").empty().hide();
    $('html, body').animate({ scrollTop: 0 }, 'slow');
    
	var feeditempackage = data.d;
    if (init) {
        if (feeditempackage.Settings.Title.length == 0) {
            $("#title").hide();
            document.title = "AmpliFeeder";
        }
        else {
            $("#title").html('<a href="default.aspx">' + feeditempackage.Settings.Title + '</a>');
            document.title = feeditempackage.Settings.Title;
        }

        if (feeditempackage.Settings.Tagline.length == 0) {
            $("#tagline").hide();
        }
        else {
            $("#tagline").html(feeditempackage.Settings.Tagline);
        }

        if (feeditempackage.Settings.About.length == 0) {
            $("#about").hide();
        }
        else {
            $("#about").html(feeditempackage.Settings.About);
            var meta = $('meta')[0];
            if (meta) {
                meta.name = 'description';
                meta.content = feeditempackage.Settings.About;
            }
        }
/*
        if (feeditempackage.Settings.CustomCSS.length > 0) {
            $("head").append('<style>' + feeditempackage.Settings.CustomCSS + '</style>');
        }*/

        init = false;
    }

    PageCount = feeditempackage.PageCount;

    $.each(feeditempackage.FeedItems, function(i, item) { ProcessFeedItem(item); });

    $("#TemplateItemsHolder").fadeIn(300);

    $("#pager").pager({ pagenumber: PageNumber, pagecount: PageCount, buttonClickCallback: PagerClick });

    if ($("body").is(":hidden"))
    {
        $("body").fadeIn(300);
    }

    if (typeof MasterPageRendered == 'function') { MasterPageRendered(); }
};

ProcessFeedItem = function(item) {
	
    var $f = $("#TemplateDump").find("." + item.SourceTypeName).clone();
    if ($f.length == 0) {
        $("#TemplateItemsHolder").append("<br/>Cannot find " + item.SourceTypeName + " item template. You may need to create one or get an updated version of this theme<br/>");  
    }
    else {
        $("#TemplateItemsHolder").append(RenderItemTemplate($f, item));
    }
};

LoadAndRenderFeatures = function() {

    $(".Feature").each(function(i,item){ LoadFeature(item)})

}

LoadFeature = function(destination) {
    var count = $(destination).find(".itemcount").text();
    var type = $(destination).find(".itemtype").text();

    var parameterObject = '{"itemtype":"' + type + '", "numberToReturn":"' + count + '"}';
    $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        timeout: 25000,
		{% if cname %}		
        url: "/UIService.asmx/GetFeature",
		{% else %}
        url: "/{{user.username}}/UIService.asmx/GetFeature",
		{% endif %}
        data: parameterObject,
        success: function(msg) { FeatureLoaded(destination, msg) },
        error: function(XMLHttpRequest, textStatus, errorThrown) { AjaxFailure(XMLHttpRequest, textStatus, errorThrown) }
    });
    
}

FeatureLoaded = function(destination,data) {
    var items = data.d 

    if (items.count == 0) {
        $(destination).hide();
        return;
    }

    var type = $(destination).find(".itemtype").text();
    var $f = $("#TemplateDump").find("." + type).clone();
    var destparent = $(destination).parent();
    destparent.empty();

    $.each(items, function(i, item) { RenderFeature(destparent, item, type, $f); });
}

RenderFeature = function(destparent, item, type, $f) {
    if ($f.length == 0) {
        $(destparent).append("<br/>Cannot find " + type + " feature template. You may need to create one or get an updated version of this theme<br/>");
    }
    else {
        $(destparent).append(RenderItemTemplate($f, item));
    }

}

LoadAndRenderTags = function() {

    $("#TagList").mouseover(function() { document.body.style.cursor = "pointer"; }).mouseout(function() { document.body.style.cursor = "auto"; });

    var parameterObject = '{"TagPage":"' + TagPage + '"}';
	{% if cname %}
    AjaxManager(parameterObject, "/UIService.asmx/GetTags", RenderTags, AjaxFailure);
	{% else %}
    AjaxManager(parameterObject, "/{{user.username}}/UIService.asmx/GetTags", RenderTags, AjaxFailure);
	{% endif %}
};

RenderTags = function(data) {
	var items =  data.d ;

    if (items.count == 0) {
        $("#tagtitle").hide();
        return;
    }

    $("#TagList").empty();
    $.each(items, function(i, item) { RenderTag(item); });

    $("<div id='tagpager' >more...</div>").click(function() { TagPage = TagPage + 1; LoadAndRenderTags(); }).appendTo($("#TagList"));

};

RenderTag = function(item) {

    $("<span class='tag' id='" + item.Id + "'>'" + item.Name + "'</span>").click(function() { TagClick(this.id, item.Name); }).append(" ").appendTo($("#TagList"));
};

TagClick = function(id,name) {

$("#alertbox").html("Currently just showing the items that match the tag '<strong>" + name + "</strong>'. Click here to show all items.").show();
    ItemFilterType = "Tag";
    ItemFilterArgument = id;
    PageNumber = 1;
    LoadAndRenderFeedItemPackage();
};

ChannelResetClick = function() {

    ItemFilterType = "None";
    ItemFilterArgument = "None";
    LoadAndRenderFeedItemPackage();
    $("#alertbox").hide();
};

InitializeSearch = function() {

    $SearchButton = $('<span class="btn">search</span>').click(function() { DoSearch(); }).mouseover(function() { document.body.style.cursor = "pointer"; }).mouseout(function() { document.body.style.cursor = "auto"; });
    $("#Search").append("<input type='text' id='txtsearch' />").append($SearchButton);
};

DoSearch = function() {

    ItemFilterType = "Search";
    ItemFilterArgument = encodeHTML($("#txtsearch").val());
    if (ItemFilterArgument !== "") {
        $("#txtsearch").val("");
        $("#alertbox").html("Currently just showing the items that match your search for '<strong>" + ItemFilterArgument + "</strong>'. Click here to show all items.").show();
        PageNumber = 1;
        LoadAndRenderFeedItemPackage();
    }
};

LoadAndRenderChannels = function() {

    var parameterObject = '{}'; 
	{% if cname %}
	AjaxManager(parameterObject, "/UIService.asmx/GetActiveSources", RenderChannels, AjaxFailure);
	{% else %}
    AjaxManager(parameterObject, "/{{user.username}}/UIService.asmx/GetActiveSources", RenderChannels, AjaxFailure);
	{% endif %}
    
};

RenderChannels = function(data) {

	var items = data.d 
    $.each(items, function(i, item) { RenderChannel(item); });

    if (items.length > 1 && $("#channels").length > 0) {
        RenderAllChannel();
    }
};

RenderChannel = function(item) {
	
    var $f = $("#TemplateDump").find("#ChannelTemplate").html();

    if ($f == null) {
        return;
    }
    var Idx = replaceAll($f, "${Id}", item.Id);
    var FirefoxIdx = replaceAll(Idx, "$%7BId%7D", item.Id);

    var Titlex = replaceAll(FirefoxIdx, "${Title}", item.Title);
    var FirefoxTitlex = replaceAll(Titlex, "$%7BTitle%7D", item.Title);

    var FeedUrix = replaceAll(FirefoxTitlex, "${FeedUri}", item.FeedUri);
    var FirefoxFeedUrix = replaceAll(FeedUrix, "$%7BFeedUri%7D", item.FeedUri);

    var SourceTypeNamex = replaceAll(FirefoxFeedUrix, "${SourceTypeName}", item.SourceTypeName);
    var FirefoxSourceTypeNamex = replaceAll(SourceTypeNamex, "$%7BSourceTypeName%7D", item.SourceTypeName);

    $(FirefoxSourceTypeNamex).mouseover(function() { document.body.style.cursor = "pointer"; }).mouseout(function() { document.body.style.cursor = "auto"; }).click(function() { ChannelClick(this.id, item.Title); }).appendTo($('#channels'));
};

RenderAllChannel = function() {
    var $f = $("#TemplateDump").find("#ChannelTemplate").html();

    if ($f == null) {
        return;
    }
    var Idx = replaceAll($f, "${Id}", "All");
    var FirefoxIdx = replaceAll(Idx, "$%7BId%7D", "All");

    var Titlex = replaceAll(FirefoxIdx, "${Title}", "");
    var FirefoxTitlex = replaceAll(Titlex, "$%7BTitle%7D", "");

    var FeedUrix = replaceAll(FirefoxTitlex, "${FeedUri}", "#");
    var FirefoxFeedUrix = replaceAll(FeedUrix, "$%7BFeedUri%7D", "#");

    var SourceTypeNamex = replaceAll(FirefoxFeedUrix, "${SourceTypeName}", "All");
    var FirefoxSourceTypeNamex = replaceAll(SourceTypeNamex, "$%7BSourceTypeName%7D", "All");

    $(FirefoxSourceTypeNamex).mouseover(function() { document.body.style.cursor = "pointer"; }).mouseout(function() { document.body.style.cursor = "auto"; }).click(function() { ChannelResetClick(); }).appendTo($('#channels'));
};

ChannelClick = function(id,name) {

    ItemFilterType = "Source";
    ItemFilterArgument = id;
    $("#alertbox").html("Currently just showing the items that come from <strong>" + name + "</strong>. Click here to show all items.").show();
    PageNumber = 1;
    LoadAndRenderFeedItemPackage();
};

checkForEnter = function(event) {

    if (event.keyCode == 13) {
        event.preventDefault();
        DoSearch();
    }
};

RenderItemTypes = function() {

    if ($("#pages").length > 0)
    {
        RenderHomeItemType();
        RenderItemType("Bookmark");
        RenderItemType("Image");
        RenderItemType("Note");
        RenderItemType("Video");
        RenderItemType("Post");
    }
}

RenderItemType = function(sourcetypename) {
    var $f = $("#TemplateDump").find("#ItemTypeTemplate").html();
	
    if ($f == null) {
        return;
    }
    var Idx = replaceAll($f, "${Id}", sourcetypename);
    var FirefoxIdx = replaceAll(Idx, "$%7BId%7D", sourcetypename);

    var Titlex = replaceAll(FirefoxIdx, "${Title}", sourcetypename);
    var FirefoxTitlex = replaceAll(Titlex, "$%7BTitle%7D", sourcetypename);

    var SourceTypeNamex = replaceAll(FirefoxTitlex, "${SourceTypeName}", sourcetypename);
    var FirefoxSourceTypeNamex = replaceAll(SourceTypeNamex, "$%7BSourceTypeName%7D", sourcetypename);

    $(FirefoxSourceTypeNamex).mouseover(function() { document.body.style.cursor = "pointer"; }).mouseout(function() { document.body.style.cursor = "auto"; }).click(function() { ItemTypeClick(sourcetypename); }).appendTo($('#pages'));
}

RenderHomeItemType = function() {
    var $f = $("#TemplateDump").find("#ItemTypeTemplate").html();

    if ($f == null) {
        return;
    }
    var Idx = replaceAll($f, "${Id}", "Home");
    var FirefoxIdx = replaceAll(Idx, "$%7BId%7D", "Home");

    var Titlex = replaceAll(FirefoxIdx, "${Title}", "item");
    var FirefoxTitlex = replaceAll(Titlex, "$%7BTitle%7D", "item");

    var SourceTypeNamex = replaceAll(FirefoxTitlex, "${SourceTypeName}", "Home");
    var FirefoxSourceTypeNamex = replaceAll(SourceTypeNamex, "$%7BSourceTypeName%7D", "Home");

    $(FirefoxSourceTypeNamex).mouseover(function() { document.body.style.cursor = "pointer"; }).mouseout(function() { document.body.style.cursor = "auto"; }).click(function() { ChannelResetClick(); }).appendTo($('#pages'));
}

ItemTypeClick = function(sourcetypename) {
    ItemFilterType = "ItemType";
    ItemFilterArgument = sourcetypename;
    $("#alertbox").html("Currently viewing the <strong>" + sourcetypename + "</strong> page. Click here to show all items.").show();
    PageNumber = 1;
    LoadAndRenderFeedItemPackage();
}