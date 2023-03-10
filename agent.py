import os
import time
import numpy as np
import tensorflow as tf
from tensorflow.compat.v1.train import AdamOptimizer

import utils
from network import *
from learner import *

# A3CAgent 클래스
class A3CAgent():
    def __init__(self, code, model, n_steps, chart_size, balance_size, action_size, reuse_model=None, 
                    chart_data=None, training_data=None, initial_balance=100000000, 
                    min_trading_price=100000, max_trading_price=1000000, lr=1e-4):
        self.code = code
        self.model = model
        self.chart_data = chart_data 
        self.training_data = training_data
        self.initial_balance = initial_balance
        self.min_trading_price = min_trading_price
        self.max_trading_price = max_trading_price 
        self.action_size = action_size
        self.n_steps = n_steps
        self.chart_size = chart_size
        self.balance_size = balance_size
        # A3C 하이퍼파라미터
        self.lr = lr
        self.discount_factor = 0.99
        # 쓰레드의 갯수
        self.threads = 16
        # 전역 신경망 생성
        if self.model == 'LSTMDNN' :
            self.global_model = LSTM_DNN_AC(action_size, n_steps, chart_size, balance_size)
            # 모델 입력 데이터 정의 : [(n_steps, chart_columns_shape), balance_state_shape]
            inputs = [tf.TensorShape((None, n_steps, chart_size)), tf.TensorShape((None, balance_size))]
            # 모델 할당 및 전역 신경망 가중치 초기화 
            self.global_model.build(inputs)
            # 모델 가중치 저장 경로 설정
            self.model_path = os.path.join(utils.BASE_DIR, 'model', self.model, f'{self.model}_{n_steps}')
        
        if self.model == 'DNN' :
            self.global_model = DNN_AC(action_size, chart_size, balance_size)
            # 모델 입력 데이터 정의 : [chart_columns_shape, balance_state_shape]
            inputs = [tf.TensorShape((None, chart_size)), tf.TensorShape((None, balance_size))]
            # 모델 할당 및 전역 신경망 가중치 초기화 
            self.global_model.build(inputs)
            # 모델 가중치 저장 경로 설정
            self.model_path = os.path.join(utils.BASE_DIR, 'model', self.model, self.model)
        
        # 인공신경망 업데이트하는 옵티마이저 함수 생성
        self.optimizer = AdamOptimizer(self.lr, use_locking=True)
        
        # 모델 업데이트시 저장한 모델 재 사용
        if reuse_model :
            self.global_model.load_weights(self.model_path)

    # 모델 훈련 및 업데이트(--mode : train, update)
    def train(self):
        # 쓰레드 수 만큼 Runner 클래스 생성
        runners = [Learner(self.code, self.model, self.chart_data, self.training_data, self.initial_balance, self.min_trading_price, 
                            self.max_trading_price, self.action_size, self.n_steps, self.chart_size, 
                            self.balance_size, self.global_model, self.optimizer, 
                            self.discount_factor) for _ in range(self.threads)]
        # 각 쓰레드 실행
        for i, runner in enumerate(runners):
            print("START WORKER #{:d}".format(i))
            runner.start()

        # 30분 (1800초)에 한 번씩 모델을 저장
        while True:
            self.global_model.save_weights(self.model_path, save_format="tf")
            time.sleep(60 * 30)
    
    # 모델 테스트(--mode : test)
    def test(self) :
        runner = Learner(self.code, self.model, self.chart_data, self.training_data, self.initial_balance, self.min_trading_price, 
                            self.max_trading_price, self.action_size, self.n_steps, self.chart_size, 
                            self.balance_size, self.global_model, self.optimizer, 
                            self.discount_factor)
        print('START TEST')
        runner.test()
    
    # 랜덤 행동 결정(--mode : monkey)
    def monkey(self) :
        runner = Learner(self.code, self.model, self.chart_data, self.training_data, self.initial_balance, self.min_trading_price, 
                            self.max_trading_price, self.action_size, self.n_steps, self.chart_size, 
                            self.balance_size, self.global_model, self.optimizer, 
                            self.discount_factor)
        print('START MONKEY')
        runner.monkey()