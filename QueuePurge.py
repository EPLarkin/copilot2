# ======================================================================
# Delete all messages from a specific Queue Point in WebSphere ND 8.5.5
# and send an email notification with the number of messages deleted.
# ======================================================================

# --- USER CONFIGURATION ---
busName        = "YourBusName"
queuePointName = "YourQueuePointName"
meName         = "YourMessagingEngineName"   # Example: "ME1"

# Email settings
smtpHost       = "smtp.yourcompany.com"
smtpPort       = 25
mailFrom       = "websphere@yourcompany.com"
mailTo         = "you@yourcompany.com"
smtpUser       = ""
smtpPassword   = ""
subject        = "WebSphere Queue Purge Completed"
# ======================================================================

import sys
import javax.mail
import javax.mail.internet
import java.util.Properties


# Validate required configuration values before attempting the purge.
def validate_config():
    if not busName or busName == "YourBusName":
        raise ValueError("busName is not configured.")
    if not queuePointName or queuePointName == "YourQueuePointName":
        raise ValueError("queuePointName is not configured.")
    if not meName or meName == "YourMessagingEngineName":
        raise ValueError("meName is not configured.")
    if not smtpHost or smtpHost == "smtp.yourcompany.com":
        raise ValueError("smtpHost is not configured.")
    if not mailFrom or mailFrom == "websphere@yourcompany.com":
        raise ValueError("mailFrom is not configured.")
    if not mailTo or mailTo == "you@yourcompany.com":
        raise ValueError("mailTo is not configured.")

    try:
        int(smtpPort)
    except (TypeError, ValueError):
        raise ValueError("smtpPort must be an integer.")


# Safely convert a purge result into an integer for reporting.
def parse_count(value):
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


# Send an email notification.
def send_email(email_subject, body_text):
    props = Properties()
    props.put("mail.smtp.host", smtpHost)
    props.put("mail.smtp.port", str(smtpPort))

    if smtpUser:
        props.put("mail.smtp.auth", "true")

    session = javax.mail.Session.getInstance(props, None)

    msg = javax.mail.internet.MimeMessage(session)
    msg.setFrom(javax.mail.internet.InternetAddress(mailFrom))
    msg.setRecipient(javax.mail.Message.RecipientType.TO,
                     javax.mail.internet.InternetAddress(mailTo))
    msg.setSubject(email_subject)
    msg.setText(body_text)

    transport = session.getTransport("smtp")
    if smtpUser:
        transport.connect(smtpHost, smtpUser, smtpPassword)
    else:
        transport.connect()
    transport.sendMessage(msg, msg.getAllRecipients())
    transport.close()


# Main execution flow.
def main():
    try:
        validate_config()

        # Find the SIBMessagingEngine MBean
        meObjectName = AdminControl.queryNames(
            'type=SIBMessagingEngine,name=' + meName + ',*'
        )

        if meObjectName is None or len(meObjectName) == 0:
            raise ValueError("Messaging Engine not found: " + meName)

        print "Found Messaging Engine MBean:"
        print meObjectName

        # Build the purge parameters
        params = [busName, queuePointName]
        signature = ["java.lang.String", "java.lang.String"]

        print "Purging messages from Queue Point: " + queuePointName

        # Invoke the purge operation
        result = AdminControl.invoke(
            meObjectName,
            "purgeQueuePoint",
            params,
            signature
        )

        deleted_count = parse_count(result)
        if deleted_count is None:
            raise ValueError("Purge operation returned an unexpected value: " + str(result))

        print "Purge result: " + str(result)

        body = ("Queue purge completed.\n\n"
                "Bus: " + busName + "\n"
                "Queue Point: " + queuePointName + "\n"
                "Messages deleted: " + str(deleted_count) + "\n")

        send_email(subject, body)
        print "Email notification sent to: " + mailTo
        print "Completed successfully."

    except Exception, e:
        failure_body = ("Queue purge failed.\n\n"
                        "Bus: " + busName + "\n"
                        "Queue Point: " + queuePointName + "\n"
                        "Error: " + str(e) + "\n")

        try:
            send_email("WebSphere Queue Purge Failed", failure_body)
            print "Failure email notification sent to: " + mailTo
        except Exception, email_error:
            print "ERROR sending failure email: " + str(email_error)

        print "ERROR: " + str(e)
        sys.exit(1)


main()
