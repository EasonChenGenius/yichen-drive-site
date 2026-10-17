"""Verified registration helper using only synchronous fake mail in isolated tests."""
def register_email(client,service,email,name='QA',password='fixture-only-password'):
    mail=service.account_email;original=(mail.mail_ready,mail.deliver_code,mail.dispatch_delivery);captured=[]
    mail.mail_ready=lambda:True
    mail.deliver_code=lambda email,code,purpose:captured.append(code)
    mail.dispatch_delivery=lambda *args:mail.finish_delivery(*args)
    try:
        result=client.post('/api/auth/email/send-code',json={'email':email,'purpose':'register'})
        assert result.status_code==200,result.get_json()
        return client.post('/api/auth/register',json={'email':email,'name':name,'password':password,'challengeId':result.get_json()['challengeId'],'code':captured[-1]})
    finally:mail.mail_ready,mail.deliver_code,mail.dispatch_delivery=original
