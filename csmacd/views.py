from tkinter.tix import Tree
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from csmacd import csmacd
from csmacd.csmacd import CSMACD
from django.http import JsonResponse
import json


csmacd = CSMACD()

# Create your views here.
class Api(APIView):

    def __init__(self):
        self.executing = False
    

    def get(self, request, format=None):
        front_time = int(request.query_params.get('time'))
        actual_time = int(csmacd.actual_window_time)
        data = {}
        if actual_time >= front_time + 1:
            collisions_count = csmacd.get_window_time_collisions(actual_time - 1)
            data = {
                "time": actual_time,
                "new_time": actual_time,
                "successPackets": csmacd.get_window_time_success_packets(actual_time - 1),
                "collisionCounter": collisions_count,
                "packetsPerHost": csmacd.get_window_time_host(actual_time - 1),
                "collisions": csmacd.collisions,
                "successfully_packets": csmacd.successfully_transmitted_packets
            }
        else:
            data = {
                "time": front_time
            }
        print(data)
        return Response(data)   


    def post(self, request, format=None):
        csmacd.restart_simulation()
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        info = body['datas']
        simulation_time = info['time']
        print(body)
        N = int(info['hosts'])
        A = int(info['average'])
        R = int(info['speed']) * pow(10, 6)
        L = int(info['length'])
        D = int(info['distance'])
        C = 3 * pow(10, 8) # speed of light
        S = (2/float(3)) * C
        csmacd.csma_cd(N, A, R, L, D, S, simulation_time, True)
        return Response("Simulacion terminada")