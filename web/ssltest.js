function loadJSON(path, success, error)
{
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function()
    {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                if (success)
                    success(JSON.parse(xhr.responseText));
            } else {
                if (error)
                    error(xhr);
            }
        }
    };
    xhr.open("GET", path, true);
    xhr.send();
}

function sortByKey(array, key) {
    return array.sort(function(a, b) {
        var x = a[key]; var y = b[key];
        return ((x < y) ? -1 : ((x > y) ? 1 : 0));
    });
}

function displayResults(input) {
    var SSLTESTURL = "https://www.ssllabs.com/ssltest/analyze.html";
    var table = document.getElementById("resultsTable");
    data = input.results;
    var summary = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0, "X": 0 };
    var totalOrgs = data.length;
    for (var i = 0; i < totalOrgs; i++) {
	item = data[i]
	var row = table.insertRow(-1);
	var cname = row.insertCell(-1),
	    clowgrade = row.insertCell(-1);
	cname.innerHTML = '<a href="'+item.link+'">'+item.name+'</a>';
	cname.className = "orgname";
	clowgrade.innerHTML = '<span class="lowgrade"><a href="'+SSLTESTURL+'?d='+item.url+'">'+item.lowGrade+'</a></span>';
	summary[item.lowGrade[0]]++;
	clowgrade.className = "lowgrade";
	var endpoints = item.endpoints;
	var endpointcount = endpoints.length;
	if (endpointcount > 1) {
	    cname.rowSpan = endpointcount;
	    clowgrade.rowSpan = endpointcount;
	}

	if (endpointcount == 0) {
	    var thisRow = row;
	    var cscore = thisRow.insertCell(-1);
	    cscore.innerHTML = 'N/A'
	    cscore.className = "grade";
	    var crc4 = thisRow.insertCell(-1);
	    crc4.innerHTML = "N/A"
	    var cpoodle = thisRow.insertCell(-1);
	    cpoodle.innerHTML = "N/A"
	    var cbeast = thisRow.insertCell(-1);
	    cbeast.innerHTML = "N/A"
	    var cwarnings = thisRow.insertCell(-1);
	    cwarnings.innerHTML = "N/A"
	    var cstatus = thisRow.insertCell(-1);
	    cstatus.innerHTML = "No SSL support!"
	}

	for (var j = 0; j < endpointcount; j++) {
	    endpoint = endpoints[j];
	    var thisRow = (j > 0) ? table.insertRow(-1) : row;
	    var cscore = thisRow.insertCell(-1);
	    cscore.innerHTML = '<a href="'+SSLTESTURL+'?d='+item.url+'&s='+endpoint.ipAddress+'">'+endpoint.grade+'</a>'
	    cscore.className = "grade";
	    var crc4 = thisRow.insertCell(-1);
	    crc4.innerHTML = endpoint.rc4 ? "Bad" : "Good";
	    var cpoodle = thisRow.insertCell(-1);
	    cpoodle.innerHTML = endpoint.poodle ? "Bad" : "Good";
	    var cbeast = thisRow.insertCell(-1);
	    cbeast.innerHTML = endpoint.beast ? "Bad" : "Good";
	    var cwarnings = thisRow.insertCell(-1);
	    cwarnings.innerHTML = endpoint.hasWarnings ? "Has" : "Good";
	    var cstatus = thisRow.insertCell(-1);
	    cstatus.innerHTML = (endpoint.statusMessage == 'Ready') ? "" : endpoint.statusMessage;
	    if (endpoint.grade == 'X') {
		crc4.innerHTML = 'N/A';
		cpoodle.innerHTML = 'N/A';
		cbeast.innerHTML = 'N/A';
		cwarnings.innerHTML = 'N/A';
	    }
	}
    }
    var lastUpdate = document.getElementById("lastupdate");
    lastupdate.innerHTML = input.update;
    var grades = ["A", "B", "C", "D", "E", "F", "X"];
    var sumText = ""
    for (var i = 0; i < grades.length; i++) {
	numGrade = summary[grades[i]];
	if (numGrade > 0) {
	    sumText += grades[i] + ": " + numGrade + " (" + Math.round(100*numGrade/totalOrgs) +"%) ";
	}
    }
    console.log(sumText);
    var summary = document.getElementById("summary");
    summary.innerHTML = "Distribution of grades: " + sumText;
}

loadJSON('ssltest.json',
         function(data) { displayResults(data); },
         function(xhr) { console.error(xhr); }
);
