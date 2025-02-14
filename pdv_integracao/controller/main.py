
# -*- coding: utf-8 -*-
#
#    Copyright © 2019–; Brasil; IT Brasil; Todos os direitos reservados
#    Copyright © 2019–; Brazil; IT Brasil; All rights reserved
#
from datetime import datetime
import logging
from datetime import timedelta
from unidecode import unidecode
import json
import re
from odoo import http
from odoo.http import request
from math import floor
logger = logging.getLogger(__name__)
import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
from werkzeug.urls import url_decode, iri_to_uri



class IntegracaoPdv(http.Controller):

    @http.route('/produtoconsulta', type='json', auth="user", csrf=False)
    def website_produtoconsulta(self, **kwargs):
        data = request.jsonrequest
        # TODO testar aqui se e a empresa mesmo
        hj = datetime.now()
        hj = hj - timedelta(days=10)
        hj = datetime.strftime(hj,'%Y-%m-%d %H:%M:%S')
        prod_tmpl = http.request.env['product.template'].sudo().search([
            ('write_date', '>=', hj),
            ('sale_ok', '=', True)])
        prod_ids = []
        prd_ids = set()
        for pr in prod_tmpl:
            prd_ids.add(pr.id)

        if len(prd_ids):
            prod_ids = http.request.env['product.product'].sudo().search([
                ('product_tmpl_id','in',list(prd_ids))])
        #print ('Qtde de Produtos %s\n' %(str(len(prod_ids))))
        lista = []
        for prd in prod_ids:
            prod = {}
            ncm = ''
            if prd.fiscal_classification_id:
                ncm = prd.fiscal_classification_id.code
                if ncm:
                    ncm = re.sub('[^0-9]', '', ncm)
            if ncm and len(ncm) > 8:
                ncm = '00000000'
            prod['codproduto'] = prd.id
            prod['unidademedida'] = prd.uom_id.name.strip()[:2]
            produto = prd.name.strip()
            produto = produto.replace("'"," ")
            produto = unidecode(produto)
            prod['produto'] = produto
            prod['valor_prazo'] = prd.list_price
            data_alt = prd.write_date
            data_alterado = data_alt + timedelta(hours=+3)
            prod['datacadastro'] = datetime.strftime(data_alterado,'%m/%d/%Y %H:%M:%S')
            if prd.default_code:
                codpro = prd.default_code.strip()
            else:
                codpro = str(prd.id)
            prod['codpro'] = codpro[:15]
            if prd.origin:
                prod['origem'] = prd.origin
            prod['ncm'] = ncm
            prod['usa'] = 'S'
            if prd.barcode and len(prd.barcode) < 14:
                prod['cod_barra'] = prd.barcode.strip()
            lista.append(prod)



        # Itens inativos
        prod_tmpl = http.request.env['product.template'].sudo().search([
            ('write_date', '>=', hj),
            ('sale_ok', '=', True),
            ('active' ,'=', False)])
        prd_ids = set()
        prod_ids = []
        for pr in prod_tmpl:
            prd_ids.add(pr.id)

        if prod_tmpl:
            prod_ids = http.request.env['product.product'].sudo().search([
                ('product_tmpl_id','in',list(prd_ids)),
                ('active','=', False)])       
        for prd in prod_ids:
            prod = {}
            prod['codproduto'] = prd.id
            data_alt = prd.write_date
            data_alterado = data_alt + timedelta(hours=+3)
            prod['datacadastro'] = datetime.strftime(data_alterado,'%m/%d/%Y %H:%M:%S')
            prod['usa'] = 'N'
            produto = prd.name.strip()
            produto = produto.replace("'"," ")
            produto = unidecode(produto)
            prod['produto'] = produto
            if prd.default_code:
                codpro = prd.default_code.strip()
            else:
                codpro = str(prd.id)
            prod['codpro'] = codpro[:15]

            lista.append(prod)
        return json.dumps(lista)      

    @http.route('/cliente_cnpj', type='json', auth="public", csrf=False)
    def website_cliente_cnpj(self, **kwargs):
        data = request.jsonrequest
        cnpj = re.sub('[^0-9]', '', data['params']['cnpj'])
        # TODO testar aqui se e a empresa mesmo
        cnpj = '%s.%s.%s/%s-%s' %(cnpj[:2],cnpj[2:5],cnpj[5:8],cnpj[8:12],cnpj[12:14])
        cliente = http.request.env['res.partner']

        cli_ids = cliente.sudo().search([('cnpj_cpf', '=', cnpj),])
        lista = []
        cliente = 'N'
        for partner_id in cli_ids:
            cliente = partner_id.ref
        return cliente

    @http.route('/clienteconsulta', type='json', auth="user", csrf=False)
    def website_clienteconsulta(self, **kwargs):
        data = request.jsonrequest
        # TODO testar aqui se e a empresa mesmo
        hj = datetime.now()
        hj = hj - timedelta(days=10)
        hj = datetime.strftime(hj,'%Y-%m-%d %H:%M:%S')
        cliente = http.request.env['res.partner']
        cli_ids = cliente.sudo().search([('write_date', '>=', hj), ('customer','=', True)])
        lista = []
        for partner_id in cli_ids:
            cliente = {}
            nome = partner_id.name.strip()
            nome = nome.replace("'"," ")
            nome = unidecode(nome)
            cliente['codcliente'] = partner_id.id
            cliente['nomecliente'] = nome
            cliente['razaosocial'] = nome
            cliente['tipofirma'] = 0
            cliente['segmento'] = 1
            cliente['regiao'] = 1
            cliente['codusuario'] = 1
            cliente['status'] = 1
            cliente['cnpj'] = partner_id.cnpj_cpf
            data_alt = partner_id.write_date
            data_alterado = data_alt + timedelta(hours=+3)
            cliente['data_matricula'] = datetime.strftime(data_alterado,'%m/%d/%Y %H:%M:%S')
            cliente['datacadastro'] = datetime.strftime(data_alterado,'%m/%d/%Y')            
            lista.append(cliente)
        lista_j = json.dumps(lista)
        return lista_j

    @http.route('/contasconsulta', type='json', auth="user", csrf=False)
    def website_contasconsulta(self, **kwargs):
        user_id = http.request.env['res.users'].browse([request.uid])
        data = request.jsonrequest
        cod_cliente = data['cod_cliente']
        caixa = data['caixa']
        aml_id = data['aml_id']
        cod_forma = data['cod_forma']   
        if ',' in data['valor_pago']:     
            valor_pago = data['valor_pago'].replace(',','.')
            juro = data['juro'].replace(',','.')
        else:
            valor_pago = data['valor_pago']
            juro = data['juro']
        # TODO testar aqui se e a empresa mesmo
        cc = http.request.env['account.account'].search([
            ('name', 'ilike', 'Cliente Padrao'),
            ('company_id', '=', user_id.company_id.id),
        ])
        cj = http.request.env['account.journal'].search([
            ('name', 'ilike', 'Cliente'),
            ('company_id', '=', user_id.company_id.id),
        ])        
        conta_obj = http.request.env['account.move.line']
        conta_ids = conta_obj.sudo().search([('partner_id', '=',int(cod_cliente)), 
            ('full_reconcile_id', '=', False), ('balance','!=', 0),
            ('company_id', '=', user_id.company_id.id),
            ('account_id.reconcile','=',True),
            ('account_id', '=', cc.id),
            ('journal_id', '=', cj.id),
        ], order='date_maturity')
        vlr = float(valor_pago)
        juros = float(juro)
        vlr = vlr - juros
        vlr_baixado = '0.00'
        if vlr:
            # tem valor , entao baixa
            diario = data['diario'][:2]
            diario_obj = http.request.env['account.journal']    
            diario_id = diario_obj.search([
                ('company_id', '=', user_id.company_id.id),
                ('name', 'ilike', diario)])
            if not diario:
                return 'Diario invalido'
            for conta in conta_ids:
                if vlr < 0.01:
                    continue

                # nao preciso mais disto pq 
                # baixo uma conta por vez
                #     vlr_pago = conta.debit
                #     if vlr > conta.debit:
                #         vlr_baixado =+ conta.debit
                #         vlr_pago = conta.debit
                #     else:
                #         vlr_pago = vlr
                #         vlr_baixado =+ vlr
                #     vlr -= conta.debit

                # aqui colocar pra baixar
                if conta.id == int(aml_id):
                    arp = http.request.env['account.abstract.payment']
                    # passo duas vezes o cod_forma, na segunda vai como cod_venda
                    arp.baixa_pagamentos(conta, diario_id, caixa, vlr, cod_forma, juros)
                    vlr = 0.0
            conta_ids = conta_obj.sudo().search([('partner_id', '=',int(cod_cliente)), 
                ('full_reconcile_id', '=', False), ('balance','!=', 0),
                ('company_id', '=', user_id.company_id.id),
                ('account_id.reconcile','=',True),
                ('account_id', '=', cc.id),
                ('journal_id', '=', cj.id),
            ], order='date_maturity')        
        lista = []
        for conta in conta_ids:
            #if not '4-' in conta.journal_id.name or conta.debit == 0.0:
            #    continue
            contas = {}
            nome = conta.name.strip()
            nome = nome.replace("'"," ")
            nome = unidecode(nome)
            contas['cliente'] = conta.partner_id.id
            data_fatura = datetime.strftime(conta.date,'%d/%m/%Y')
            contas['valor'] = conta.amount_residual
            contas['data_fatura'] = data_fatura
            data_vencimento = datetime.strftime(conta.date_maturity,'%d/%m/%Y')
            contas['data_vencimento'] = data_vencimento
            contas['fatura'] = conta.move_id.ref
            contas['codigo'] = conta.id
            # contas['cod_cliente'] = 1           
            lista.append(contas)
        return json.dumps(lista)

    @http.route('/usuarioconsulta', type='json', auth="user", csrf=False)
    def website_usuarioconsulta(self, **kwargs):
        data = request.jsonrequest
        # TODO testar aqui se e a empresa mesmo
        hj = datetime.now()
        hj = hj - timedelta(days=10)
        hj = datetime.strftime(hj,'%Y-%m-%d %H:%M:%S')
        user = http.request.env['res.users']
        user_ids = user.sudo().search([('write_date', '>=', hj)])
        lista = []
        for usr in user_ids:
            user = {}
            barcode = ''
            if usr.barcode:
                barcode = usr.barcode
            user['codusuario'] = usr.id
            user['nomeusuario'] = usr.name
            user['codbarra'] = barcode
            user['status'] = 1
            lista.append(user)
        return json.dumps(lista)

    @http.route('/enviasangria', type='json', auth="user", csrf=False)
    def website_enviasangria(self, **kwargs):
        #{"params": {"login": "ats@atsti.com.br", "password": "123456", "db": "21_vitton"}, "todos": [{9992, "Sangria", 1, "200,00"}, {9993, "Sangria", 1, "25,00"}]}
        user_id = http.request.env['res.users'].browse([request.uid])
        # receber todas as sangrias e reforco do caixa
        # verificar no odoo se existe       
        data = request.jsonrequest
        lista_pdv = json.loads(data['todos'])
        caixa = lista_pdv[0]['caixa']
        sg_obj = http.request.env['account.bank.statement.line']
        
        # vejo os diarios usados no PDV do Caixa aberto
        session = http.request.env['pos.session'].search([
            ('id', '=', caixa)
        ])
        lista_st = []
        for lt_st in session.statement_ids:
            lista_st.append(lt_st.id)

        for lt in lista_pdv:
            motivo = lt['motivo']
            valor = lt['valor'].replace(',','.')
            valor = float(valor)
            cod_forma = lt['codforma']
            cod_venda = int(lt['codvenda'])
            
            diario = '1-'
            if cod_venda == 2: 
                diario = motivo[:2]
            diario_obj = http.request.env['account.journal']    
            diario_id = diario_obj.search([
                ('company_id', '=', user_id.company_id.id),
                ('name', 'ilike', diario)])
            # verifica se ja foi feito
            line = sg_obj.search([
                ('ref', '=', str(cod_forma)),
                ('statement_id', 'in', (lista_st)),
            ])
            if not line:
                arp = http.request.env['account.abstract.payment']
                arp.lanca_sangria_reforco(diario_id, caixa, valor, cod_forma, cod_venda, user_id.partner_id, motivo)

    @http.route('/caixaconsulta', type='json', auth="user", csrf=False)
    def website_caixaconsulta(self, **kwargs):
        data = request.jsonrequest
        session = http.request.env['pos.session']
        ses_ids = session.sudo().search([('state', '=', 'opened')],limit=4)
        lista = []
        for ses in ses_ids:
            if 'caixa' in data:
                dados_json = json.loads(data['caixa'])
                for d in dados_json:
                    if 'SITUACAO' in d and d['SITUACAO'] == 'F' and d['CODCAIXA'] == ses.id:
                        ses.sudo().write({'venda_finalizada': True})
            caixa = {}
            hj = datetime.now()
            dta_abre = datetime.strftime(hj,'%m-%d-%Y')
            caixa['idcaixacontrole'] = ses.id
            caixa['codcaixa'] = ses.id
            caixa['codusuario'] = ses.user_id.id
            caixa['situacao'] = 'o'
            caixa['datafechamento'] = '01-01-2020'
            caixa['nomecaixa'] = ses.name
            caixa['dataabertura'] = dta_abre
            caixa['valorabre'] = ses.cash_register_balance_start
            lista.append(caixa)
        return json.dumps(lista)

    @http.route('/pedidoconsulta', type='json', auth="user", csrf=True)
    def website_pedidoconsulta(self, **kwargs):
        data = request.jsonrequest
        # TODO testar aqui se e a empresa mesmo
        user_id = http.request.env['res.users'].browse([request.uid])
        hj = datetime.now()
        hj = hj - timedelta(days=3)
        hj = datetime.strftime(hj,'%Y-%m-%d %H:%M:%S')
        pedido = http.request.env['pos.order']
        if 'caixa' in data:
            ped_ids = pedido.sudo().search([('write_date', '>=', hj),
                ('company_id', '=', user_id.company_id.id),
                ('session_id', '=', data['caixa']),
                ], order="pos_reference desc", limit=10)
        else:
            ped_ids = pedido.sudo().search([('write_date', '>=', hj),
                ('company_id', '=', user_id.company_id.id),
                ], order="pos_reference desc", limit=10)

        if not ped_ids:
            ped_ids = pedido.sudo().search([],
                order="id desc", limit=10)
        lista = []
        ultimo = ''
        menor = 0
        maior = 0
        for p_id in ped_ids:
            if not p_id.pos_reference:
                continue
            ped = p_id.pos_reference[p_id.pos_reference.find('-')+1:]
        #     if ultimo != '':
        #         ultimo += ','
            ultimo += ped
        #     if int(ped) < menor or menor == 0:
        #         menor = int(ped)
        #     if int(ped) > maior or maior == 0:
        #         maior = int(ped)
        # if (maior - menor) > 10:
        #     menor = maior - 1
        # ultimo = '(%s) AND m.CODMOVIMENTO > %s' %(str(ultimo), str(menor))
        ped = {'pedido': str(ultimo)}

        lista.append(ped)
        return json.dumps(lista)

    @http.route('/pedidoconsultageral', type='json', auth="user", csrf=False)
    def website_pedidoconsultageral(self, **kwargs):
        data = request.jsonrequest
        # TODO testar aqui se e a empresa mesmo
        user_id = http.request.env['res.users'].browse([request.uid])
        pedido = http.request.env['pos.order']
        lista_pdv = json.loads(data['todos'])
        if 'todos' in data:
            ped_ids = pedido.sudo().search([
                ('company_id', '=', user_id.company_id.id),
                ('session_id', '=', int(data['caixa'])),
                ])            
            lista_odoo = []
            for p_id in ped_ids:
                if not p_id.pos_reference:
                    continue
                ped = p_id.pos_reference[p_id.pos_reference.find('-')+1:]
                lista_odoo.append(int(ped))
        diferenca = set(lista_pdv).difference(set(lista_odoo))
        ultimo = ''
        for pedidos in list(diferenca):
            if ultimo != '':
                ultimo += ', '
            ultimo += str(pedidos)
        ultimo = '(%s)' %(str(ultimo))
        ped = {'pedido': str(ultimo)}
        lista = []
        lista.append(ped)
        return json.dumps(lista)

    def _monta_pedido(self,dados):
        codmov = dados['CODMOVIMENTO']
        codcliente = dados['CODCLIENTE']
        caixa = dados['CODALMOXARIFADO']
        codvendedor = dados['CODVENDEDOR']
        data_sistema = dados['DATA_SISTEMA']
        coduser = dados['CODUSUARIO']
        controle = dados['CONTROLE']
        ord_name = '%s-%s' %(caixa, codmov)
        vals = {}               
        pos = http.request.env['pos.order']
        ord_ids = pos.sudo().search([
            ('session_id','=',caixa),
            ('sequence_number', '=', codmov),
        ])
        if not ord_ids:
            # insere o pedido
            # prt = http.request.env['res.partner']
            # usr = http.request.env['res.users']
            # prt_id = prt.sudo().search([
            #     ('id','=',codcliente),
            # ])
            # ven_id = usr.sudo().search([
            #     ('id','=',codvendedor),
            # ])
            # usr_id = usr.sudo().search([
            #     ('id','=',coduser),
            # ])
            # if prt_id and ven_id and usr_id:
            data_pedido = datetime.strptime(data_sistema,'%m/%d/%Y %H:%M')
            data_pedido = data_pedido + timedelta(hours=+3)
            user_id = http.request.env['res.users'].browse([request.uid])
            if 1 == 1:
                vals['name'] = ord_name
                vals['nb_print'] = 0
                vals['pos_reference'] = ord_name
                vals['session_id'] = int(str(caixa))
                # vals['pos_session_id'] = int(str(caixa))
                # vals['pricelist_id'] = session.config_id.pricelist_id.id
                vals['create_date'] = data_pedido #datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S')
                vals['date_order'] = data_pedido
                vals['sequence_number'] = codmov
                vals['partner_id'] = int(codcliente)
                vals['user_id'] = int(codvendedor)
                vals['amount_tax'] = 0.0
                vals['company_id'] = user_id.company_id.id
            """
                if cli != 1:
                    if cli == 1609:
                        cli = 1944
                    vals['partner_id'] = cli
                else:
                    vals['partner_id'] = self.env['res.partner'].search([
                        ('name','ilike','consumidor')],limit=1)[0].id
                userid = mvs[5]
                userid = self.env['res.users'].search([('id','=',userid)])
                if userid:
                    vals['user_id'] = userid.id
                if not userid:
                    vals['user_id'] = 1
                vals['fiscal_position_id'] = session.config_id.default_fiscal_position_id.id"""
            return vals

    def _monta_pedidodetalhe(self,dados_json, desconto_financeiro, total_geral):
        dados = json.loads(dados_json)
        soma_t = 0.0
        vlr_total = 0.0
        order_line = []
        desc_f = 0.0
        desconto = 0
        if desconto_financeiro:
            desc_f = desconto_financeiro / total_geral
        num_linha = len(dados)
        for md in dados:            
            if num_linha:
                try:
                    prdname = unidecode(md['DESCPRODUTO'])
                except:
                    prdname = 'Nada'
                pco = float(md['PRECO'].replace(',','.'))
                qtd = float(md['QUANTIDADE'].replace(',','.'))
                desc = float(md['VALOR_DESCONTO'].replace(',','.'))
                vlr_totprod = (pco * qtd) - desc
                vlr_total += vlr_totprod
                
                if desc > 0 or desc_f > 0:
                    teve_desconto = 's'                    
                    if num_linha > 1 and ((vlr_totprod+desc) + desc_f) > 0 and desc:
                        desconto = desc / (vlr_totprod+desc) + desc_f
                        desconto = desconto
                    else:
                        #desconto Zero, vou editar depois de gravado
                        # pra calcular o desconto correto
                        desconto = 0.0
                prd = {}
                #TODO Felicita usa o campo CORTESIA como TIPO , colocar no exporta do PDV
                #if md['CORTESIA']:
                #    prd['tipo_venda'] = md['CORTESIA']
                
                prd['product_id'] = md['CODPRODUTO']
                prd['discount'] = desconto * 100
                prd['qty'] = qtd
                prd['price_unit'] = pco
                prd['full_product_name'] = prdname
                prd['price_subtotal_incl'] = vlr_totprod
                prd['price_subtotal'] = vlr_totprod
                num_linha -= 1
                desconto = 0
                order_line.append((0, 0,prd))
        return order_line    

    def _monta_pagamento(self, dados, cliente, session, ord_name, data_ord):        
        # import pudb;pu.db
        pag_line = []
        desconto_t = 0.0
        total_g = 0.0
        troca = 0.0
        controle_troca = 0
        # sqld = 'SELECT f.CODFORMA, f.FORMA_PGTO, f.VALOR_PAGO, ' \
        #     'f.STATE, f.TROCO, f.DESCONTO from FORMA_ENTRADA f' \
        #     ' WHERE ID_ENTRADA = %s AND f.STATE = 1' %(str(mvs[0]))
        #dados = json.loads(dados['pag-1'])
        dados = json.loads(dados)
        desconto = 0
        user_id = http.request.env['res.users'].browse([request.uid])
        for pg in dados:
            pag = {}
            dsc = float(pg['DESCONTO'].replace(',','.'))
            vlr = float(pg['VALOR_PAGO'].replace(',','.'))
            dsc = round(dsc,2)
            if pg['DESCONTO']:
                desconto += dsc
                teve_desconto = 's'
            total_g += vlr + dsc
            jrn = '%s-' %(pg['FORMA_PGTO'])
            if jrn == '5-':
                jrn = '1-'
            if jrn == '9-':
                controle_troca = 1
                troca += vlr
            jrn_id = http.request.env['account.journal'].sudo().search([
                ('name','like', jrn),
                ('company_id', '=', user_id.company_id.id)
            ])[0]
            session_id = http.request.env['pos.session'].sudo().browse([session])
            if not session_id:
                return 0,0,0,0
            # for stt in session_id.payment_ids:
            #     if stt.journal_id.id == jrn_id.id:
            #         pag['payment_ids'] = stt.id
                        
            company_cxt = jrn_id.company_id.id
            # pag['account_id'] = self.env['res.partner'].browse(cliente).property_account_receivable_id.id
            pag['date'] = data_ord
            pag['amount'] = float(pg['VALOR_PAGO'].replace(',','.'))
            pag['journal_id'] = jrn_id.id
            pag['journal'] = jrn_id.id
            pag['partner_id'] = cliente
            pag['name'] = ord_name
            # pag['discount'] = desconto
            if controle_troca == 0:
                pag_line.append((0, 0,pag))
        return pag_line, desconto, troca, total_g
                
    @http.route('/pedidoinsere', type='json', auth="user", csrf=False)
    def website_pedidoinsere(self, **kwargs):
        import pudb;pu.db
        data = request.jsonrequest
        hj = datetime.now()
        hj = datetime.strftime(hj,'%m-%d-%Y')
        if 'pedido' in data:
            dados_json = json.loads(data['pedido'])
            pedido = self._monta_pedido(dados_json)
            codmov = dados_json['CODMOVIMENTO']
            caixa = dados_json['CODALMOXARIFADO']
            ord_name = '%s-%s' %(caixa, codmov)
            tem = http.request.env['pos.order'].sudo().search([
                        ('pos_reference', '=', ord_name)])
            if tem:
                return True
            desconto = 0
            total = 0
            troca = 0
            #if 'pag' in data:
            if 'pagamentos' in dados_json:
                #dados_json = json.loads(data['pag'])
                dados_j = dados_json['pagamentos']
                pagamento, desconto, troca, total = self._monta_pagamento(dados_j, 
                    pedido['partner_id'], pedido['session_id'], pedido['name'],
                    pedido['date_order'])
                if pagamento == 0 and total == 0:
                    # nao encontrou CAIXA
                    return 'Erro na importação'
            if 'itens' in dados_json:
                #dados_json = json.loads(data['det'])               
                dados_json = dados_json['itens']
                itens_pedido = self._monta_pedidodetalhe(dados_json, desconto, total)
                if troca:
                    trc_prd = http.request.env['product.template'].sudo().search([
                        ('name', 'ilike', 'desconto')])
                    prd = {}
                    if trc_prd.id:
                        prd['product_id'] = trc_prd.id
                    else:
                        prd['product_id'] = 2
                    prd['qty'] = 1
                    vlr_troca = troca * (-1)
                    prd['price_unit'] = vlr_troca
                    #prd['tipo_venda'] = tipo
                    prd['name'] = 'Troca/Devolucao'
                    # no uol 5, nao tem estas 2 linhas abaixo
                    prd['price_subtotal_incl'] = vlr_troca
                    prd['price_subtotal'] = vlr_troca
                    itens_pedido.append((0, 0,prd))
                pedido['lines'] = itens_pedido
            # no uol 5, acho q alinha abaixo tem que ficar comentada        
            pedido['amount_return'] = total
            desconto_financeiro_troca = ''
            if desconto:
                desconto = desconto*100
                desconto_financeiro_troca = 'd%s' %(str(int(desconto)))
            if troca:
                desconto_financeiro_troca += 't%s' %(str(int(desconto)))
            pedido['note'] = desconto_financeiro_troca
                            
            pedido['amount_total'] = total
            pedido['amount_paid'] = total
            # pedido['statement_ids'] = pagamento
            pos = http.request.env['pos.order']
            ord_ids = pos.sudo().create(pedido)
        return 'Sucesso'

    @http.route('/devolucao', type='json', auth="user", csrf=False)
    def website_devolucao(self, **kwargs):
        data = request.jsonrequest
        user_id = http.request.env['res.users'].browse([request.uid]) 
        nome_busca = 'DEV-' + str(data['origin'])
        dev = http.request.env['stock.picking'].sudo().search([
                        ('origin', 'like', nome_busca)
                    ]) 
        if  dev:
            return '' 
        else:
            item = []
            vals = {}
            if 'origin' in data:
                vals['origin'] = 'DEV-' + str(data['origin'])
                operacao = http.request.env['stock.picking.type'].sudo().search([
                            ('name', 'ilike', 'devolucao')
                        ])
                prd = {}
                for tipo in operacao:
                    if tipo.warehouse_id.company_id.id == user_id.company_id.id:
                        # tipo_operacao = tipo
                        vals['picking_type_id'] = tipo.id
                        vals['location_id'] = tipo.default_location_src_id.id
                        vals['location_dest_id'] = tipo.default_location_dest_id.id
                        vals['note'] = data['motivo'] 
                        prd['location_id'] = tipo.default_location_src_id.id
                        prd['location_dest_id'] = tipo.default_location_dest_id.id
                
                prd['product_id'] = data['produto']  
                prd['product_uom_qty'] = data['quantidade'] 
                prd['product_uom'] = 1
                prd['quantity_done'] = data['quantidade'] 
                prd['name'] = data['nproduto']               
                item.append((0, 0,prd))
                vals['move_ids_without_package'] = item
                
                
                pos = http.request.env['stock.picking']
                pick = pos.sudo().create(vals)
                pick.action_confirm()
                pick.action_assign()            
                pick.button_validate()
            return 'Sucesso'


