/*
  VapURL - Expiring URL service.
  Copyright (c) 2009 Aaron McBride and John Lawlor
  MIT License (see LICENSE.txt)
  https://github.com/nogwater/vapurl
*/

window.onload = function () {
  showCustomTime();
  showCustomVisit();
}

function showCustomTime()
{
  var timeSelector = document.getElementById('max_time');
  var customTime = document.getElementById('customTimeSpan');
  if (timeSelector.value == '-1')
  {
    customTime.style.display = 'block';
  }
  else
  {
    customTime.style.display = 'none';
  }
  
}

function showCustomVisit()
{
  var visitsSelector = document.getElementById('max_visits');
  var customVisits = document.getElementById('customVisitsSpan');
  if (visitsSelector.value == '-1')
  {
    customVisits.style.display = 'block';
  }
  else
  {
    customVisits.style.display = 'none';
  }
}

function validate()
{
  var visitsSelector = document.getElementById('max_visits');
  var timeSelector = document.getElementById('max_time');
  var customVisit = document.getElementById('custom_visits');
  var customTime = document.getElementById('custom_time');
  var url = document.getElementById('url');
  
  var hasErrors = false;
  
  var errorVisit = document.getElementById('customVisitError');
  var errorTime = document.getElementById('customTimeError');
  var errorUrl = document.getElementById('urlError');
  
  if (visitsSelector.value != '-1')
  {
    customVisit.value = '1';
  }
  else
  {
    customVisit.value = customVisit.value.replace(/,/g, '');
  }
  
  if(visitsSelector.value == '-1' && (customVisit.value < 1 || customVisit.value > 1000000 ))
  {
    hasErrors = true;
    errorVisit.style.display = 'block';
  }
  else
  {
    errorVisit.style.display = 'none';
  } 
  
  if (timeSelector.value != '-1')
  {
    customTime.value = '7';
  }
  else
  {
    customTime.value = customTime.value.replace(/,/g, '');
  }
  
  if(timeSelector.value == '-1' && (customTime.value < 1 || customTime.value > 1000))
  {
    hasErrors = true;
    errorTime.style.display = 'block';
  }
  else
  {
    errorTime.style.display = 'none';
  }
  
  if(url.value.indexOf('http://http://') == 0 || url.value.indexOf('http://https://') == 0)
  {
    url.value = url.value.substr(7);
  }
  
  if((url.value.length == 0) || url.value == 'http://')
  {
    errorUrl.style.display = 'block';
    hasErrors = true;
  }
  else
  {
    errorUrl.style.display = 'none';
  }

  return !hasErrors;
}