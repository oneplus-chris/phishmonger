import tornado.web
import tornado.gen
from models.campaign import Campaign
import models.driver as driver
import rethinkdb as r
import datetime
from tornado.concurrent import Future
from services.message import Message

connection = r.connect(host='localhost', port=28015, db="phishmonger")

class CampaignsHandler(tornado.web.RequestHandler):

    @tornado.gen.coroutine
    def get(self, instance=None):
        conn = yield connection
        messages = self.getMessages()
        name = ""
        verb = "Create New Campaign"
        campaigns = []
        if instance is None:#index
            cursor = yield r.table('Campaign').run(conn)
            while (yield cursor.fetch_next()):
                campaign = yield cursor.next()
                campaigns.append(campaign)
        else:#read
            campaigns = yield self.getCampaign(instance)
            specific = campaigns[0]
            name = "{0}".format(campaigns[0].name)
            verb = "Update Campaign {0}".format(name)
        if campaigns is None:
            messages.append('No Campaigns to Display!')
            campaigns = []
        self.render('campaign/index.html', campaigns=campaigns, messages=messages, name=name, verb=verb)


    @tornado.gen.coroutine
    def post(self, instance=None):
        conn = yield connection
        messages = self.getMessages()
        name = ""
        data = self.getSpecificCampaign(default=None)
        data['date_started'] = datetime.datetime.now().strftime('%a %b %d %H:%M:%S %Y')
        campaigns = []
        if instance is None:#create
            newcampaign = yield r.table("Campaign").insert(data).run(conn)
            self.launchCampaign(newcampaign['generated_keys'][0])
            cursor = yield r.table('Campaign').run(conn)
            while (yield cursor.fetch_next()):
                campaign = yield cursor.next()
                campaigns.append(campaign)
            messages.append("Successfully created campaign {0}!".format(data['name']))
        else:#update
            campaigns = yield self.getCampaign(instance)
            name = "{0}".format(campaigns[0].name)
            messages.append("Successfully updated campaign {0}!".format(data['name']))
        if campaigns is None:
            messages.append('No Campaigns to Display!')
            campaigns = []
        self.render('campaign/index.html', campaigns=campaigns, messages=messages, name=name, verb="Create New Campaign")

    def getSpecificCampaign(self, default=''):
        return {
        'name' : self.get_argument('name',default,strip = True),
        'date_started' : self.get_argument('date_started',default,strip = True),
        'targets' : self.get_argument('targets',default,strip = True),
        }

    # def delete(self, instance=None):
    #     campaigns = yield self.listCampaigns()
    #     if campaigns is None:
    #         campaigns = []
    #     self.render('campaign/index.html', campaigns=campaigns)

    def getMessages(self):
        messages = []
        return messages

    @tornado.gen.coroutine
    def getCampaign(self, id):
        conn = yield connection
        Campaign().get(conn, {'id':id})

    @tornado.gen.coroutine
    def launchCampaign(self, campaign_id):
        conn = yield connection
        campaign = yield r.table("Campaign").get(campaign_id).run(conn)
        target_group = campaign['targets']
        responses = []
        conn = yield connection
        cursor = yield r.table("Target").filter({'group': target_group}).run(conn)
        while (yield cursor.fetch_next()):
            target = yield cursor.next()
            data = {
                'campaign_id' : campaign_id,
                'target_id' : target['id'],
                'status' : 0
            }
            response = yield r.table("Response").insert(data).run(conn)
            response_id = response["generated_keys"][0]
            html = self.htmlMessage(target, response_id)
            msg = Message(target['email'], "You have an important Document waiting in Office 365", html)
            msg.send()
            responses.append(response_id)
        yield r.table("Campaign").get(campaign_id).update({'responses' : responses}).run(conn)
        campaign = yield r.table("Campaign").get(campaign_id).run(conn)

    def htmlMessage(self, target, response_id):
        root = "http://128.138.202.39:8080"
        return "Attention <b>{0} {1}</b>,<br/>recent changes to the Microsoft Office activedirectory platform requires a change in your password. <br/> Please sign in to your Microsoft Office 365 account <a href=\"{2}/phish/{3}\">here</a><br/>Thank you for your patience,<br/>Microsoft Support".format(target['fname'], target['lname'], root,response_id)
