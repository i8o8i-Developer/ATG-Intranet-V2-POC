def text_template(name, position_name, title, message):
    return """Hi {},
    Across The Globe (ATG) is pleased to extend you an offer for {} Intern ({}). Kindly click on this link to view, download and accept your offer.
    {}
    Should you have any doubts related to the offer or onboarding, kindly consult your Hiring Manager.
    Congratulations!
    Team ATG.""".format(name, position_name, title, message)


def html_template(name, position_name, title, message, company_logo):
    return """<!DOCTYPE html>
    <html lang="en">
    <head>
    </head>
    <body>
    <div class="container" style="background:#F5F5F5;font-size:18px;font-family:'Helvetica';text-align:center;border:0.5px solid black;border-radius:20px;padding: 50px 20px" >
        <center>{}</center>
        <h4>Hi {},</h4>
        <div>Across The Globe (ATG) is pleased to extend you an offer for {} Intern ({}). Kindly click on this link to view, download and accept your offer.</div>
        <br>
        <button style="background-color: #4CAF50;
                       border: none;
                       color: white;
                       padding: 15px 32px;
                       text-align: center;
                       text-decoration: none;
                       display: inline-block;
                       font-size: 16px;">

                       <a href= "{}" target="_blank" style="text-decoration:none;color:white">CLICK HERE</a>       
        </button>
        <br><br>
        <span>Should you have any doubts related to the offer or onboarding, kindly consult your Hiring Manager.</span>
        <br>
        <span>Congratulations!</span>
        <br>
        <span>Team ATG.</span>
        
        <p style="color:#ff0000d6; text-align:left;">PS: In case 'Click Here' doesn't work copy & paste the following link in your address bar
        <span style="color:blue; word-break:break-word;">{}</span>
        </p>
    </body>
    </html>
    </div>""".format(company_logo, name, position_name, title, message, message)


def reminder_html_template(name, offer_date, position_name, title):
    return """<!DOCTYPE html>
    <html lang="en">
    <head>
    </head>
    <body>
    <div class="container" style="background:#F5F5F5;font-size:18px;font-family:'Helvetica';text-align:center;border:0.5px solid black;border-radius:20px;padding: 50px 20px" >
        <center><img src="https://i.postimg.cc/N0JT86NC/poppins-logo-full.png" alt="" style="margin:10px"></center>
        <h4>Hi {},</h4>
        <div>I hope this email finds you well. We wanted to kindly remind you that we have not yet received your formal acceptance for the offer we extended to you on {} for {} Intern ({}).
         We are excited about the possibility of you joining our team and look forward to your response.</div>
        <br>
        <br><br>
        <span>Should you have any doubts related to the offer or onboarding, kindly consult your Hiring Manager.</span>
        <br>
        <span>Congratulations!</span>
        <br>
        <span>Team ATG.</span>
        
    </body>
    </html>
    </div>""".format(name, offer_date, position_name, title)


def reminder_text(name, offer_date, position_name, title):
    return """Hi {},
    I hope this email finds you well. We wanted to kindly remind you that we have not yet received your formal acceptance for the offer we extended to you on {} for {} Intern ({}).
         We are excited about the possibility of you joining our team and look forward to your response.
    Should you have any doubts related to the offer or onboarding, kindly consult your Hiring Manager.
    Congratulations!
    Team ATG.""".format(name, offer_date, position_name, title)