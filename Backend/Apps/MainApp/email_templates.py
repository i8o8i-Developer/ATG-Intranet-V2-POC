def text_template(name, position_name, title, message):
    return f"Hello {name},\n\n{title}\n{position_name}\n\n{message}"


def html_template(name, position_name, title, message, company_logo=""):
    return f"<h1>{title}</h1><p>Hello {name},</p><p>{position_name}</p><p>{message}</p>{company_logo}"


def reminder_text(name, offer_date, position_name, title):
    return f"Hello {name}, Your {position_name} Offer {title} Is Ending Since {offer_date}."


def reminder_html_template(name, offer_date, position_name, title):
    return f"<p>Hello {name}, Your <strong>{position_name}</strong> Offer {title} Is Ending Since {offer_date}.</p>"