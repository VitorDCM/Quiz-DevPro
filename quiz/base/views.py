from django.db.models import Sum
from django.shortcuts import render, redirect
from django.utils.timezone import now

from quiz.base.forms import AlunoForm
from quiz.base.models import Pergunta, Aluno, Resposta


def home(req):
    if req.method == 'POST':

        email = req.POST['email']
        try:
            aluno = Aluno.objects.get(email=email)
        except Aluno.DoesNotExist:
            formulario = AlunoForm(req.POST)
            if formulario.is_valid():
                aluno = formulario.save()
                req.session['aluno_id'] = aluno.id
                return redirect('/perguntas/1')
            else:
                contexto = {'formulario': formulario}
                return render(req, 'base/home.html', contexto)
        else:
            req.session['aluno_id'] = aluno.id
            return redirect('/perguntas/1')
    return render(req, 'base/home.html')

PONTUACAO_MAXIMA = 1000


def perguntas(req, indice):
    try:
        aluno_id = req.session['aluno_id']
    except KeyError:
        return redirect('/')
    else:
        try:

            pergunta = Pergunta.objects.filter(disponivel=True).order_by('id')[indice - 1]
        except IndexError:
            return redirect('/classificacao')
        else:
            contexto = {'indice_questao': indice, 'pergunta': pergunta}
            if req.method == 'POST':
                resposta_indice = int(req.POST['resposta_indice'])
                if (resposta_indice == pergunta.alternativa_correta):
                    try:
                        data_primeira_resposta = Resposta.objects.filter(pergunta=pergunta).order_by('respondida_em')[0].respondida_em
                    except IndexError:
                        Resposta(aluno_id=aluno_id, pergunta=pergunta, pontos=PONTUACAO_MAXIMA).save()
                    else:
                        diferenca_tempo = now() - data_primeira_resposta
                        diferenca_segundos = diferenca_tempo.total_seconds()
                        pontos = max(PONTUACAO_MAXIMA - diferenca_segundos, 10)
                        Resposta(aluno_id=aluno_id, pergunta=pergunta, pontos=pontos).save()
                    return redirect(f'/perguntas/{indice+1}')
                contexto['resposta_indice'] = resposta_indice

            return render(req, 'base/game.html', context=contexto)


def classificacao(req):
    try:
        aluno_id = req.session['aluno_id']
    except KeyError:
        return redirect('/')
    else:
        pontos_dct = Resposta.objects.filter(aluno_id=aluno_id).aggregate(Sum('pontos'))
        pontuacao_do_aluno = pontos_dct['pontos__sum']
        pontuacao = Resposta.objects.values('aluno').annotate(Sum('pontos')).filter(pontos__sum__gt = pontuacao_do_aluno).count()
        classificacao = Resposta.objects.values('aluno', 'aluno__nome').annotate(Sum('pontos')).order_by('-pontos__sum')[:5]
        context={'pontuacao_do_aluno': pontuacao_do_aluno, 'pontos': pontuacao + 1, 'classificacao': classificacao}
    return render(req, 'base/classificacao.html', context)

