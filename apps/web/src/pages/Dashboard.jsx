import { useMutation } from "@tanstack/react-query";
import { PlusCircle } from "lucide-react";
import { useForm } from "react-hook-form";

import api from "../lib/api";
import { useProjectStore } from "../store/useProjectStore";

function gerarCodigoProjeto() {
  const sufixo = Date.now().toString().slice(-6);
  return `WEB-${sufixo}`;
}

export function Dashboard() {
  const { projetoAtivo, setProjetoAtivo } = useProjectStore();
  const {
    register,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm({
    defaultValues: {
      nome: "Projeto Teste",
      localidade: "Bangu",
      tipoProjeto: "Ligacao Nova",
    },
  });

  const mutation = useMutation({
    mutationFn: async (values) => {
      const payload = {
        codigo: gerarCodigoProjeto(),
        nome: values.nome,
        localidade: values.localidade,
        checklist_triagem: {
          tipo_projeto: values.tipoProjeto,
          recebeu_leitura_trafo_maxima: false,
          possui_fotos_campo: false,
          comparou_com_street_view: false,
          comparou_com_desenho_recebido: false,
        },
        evidencias: [],
      };

      const response = await api.post("/projetos/", payload);
      return response.data;
    },
    onSuccess: (data) => {
      setProjetoAtivo(data);
    },
  });

  const onSubmit = (values) => mutation.mutateAsync(values);

  return (
    <section
      style={{
        background: "white",
        borderRadius: "12px",
        boxShadow: "0 4px 14px rgba(15, 23, 42, 0.08)",
        padding: "20px",
      }}
    >
      <h1 style={{ marginTop: 0, marginBottom: "12px" }}>Intake / Triagem</h1>
      <p style={{ marginTop: 0, color: "#475569" }}>
        Cria rapidamente um projeto para iniciar o fluxo operacional.
      </p>

      <form onSubmit={handleSubmit(onSubmit)} style={{ display: "grid", gap: "12px", maxWidth: "460px" }}>
        <label style={{ display: "grid", gap: "6px" }}>
          Nome do Projeto
          <input
            {...register("nome", { required: true, minLength: 3 })}
            style={{ padding: "10px", border: "1px solid #cbd5e1", borderRadius: "8px" }}
          />
        </label>

        <label style={{ display: "grid", gap: "6px" }}>
          Localidade
          <input
            {...register("localidade", { required: true, minLength: 3 })}
            style={{ padding: "10px", border: "1px solid #cbd5e1", borderRadius: "8px" }}
          />
        </label>

        <label style={{ display: "grid", gap: "6px" }}>
          Tipo de Projeto
          <select
            {...register("tipoProjeto", { required: true })}
            style={{ padding: "10px", border: "1px solid #cbd5e1", borderRadius: "8px" }}
          >
            <option value="Ligacao Nova">Ligacao Nova</option>
            <option value="Robustez BT">Robustez BT</option>
            <option value="Clandestinos">Clandestinos</option>
          </select>
        </label>

        <button
          type="submit"
          disabled={isSubmitting || mutation.isPending}
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "8px",
            border: 0,
            borderRadius: "8px",
            padding: "11px 14px",
            background: "#1d4ed8",
            color: "white",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          <PlusCircle size={16} />
          Criar Novo Projeto
        </button>
      </form>

      {mutation.isSuccess && projetoAtivo ? (
        <p
          data-testid="project-created-success"
          style={{
            marginTop: "16px",
            padding: "10px 12px",
            borderRadius: "8px",
            background: "#dcfce7",
            color: "#166534",
            fontWeight: 600,
          }}
        >
          Projeto criado com sucesso. ID: {projetoAtivo.id}
        </p>
      ) : null}

      {projetoAtivo ? (
        <p
          data-testid="active-project-id"
          style={{
            marginTop: "10px",
            padding: "10px 12px",
            borderRadius: "8px",
            background: "#e0f2fe",
            color: "#0c4a6e",
            fontWeight: 600,
          }}
        >
          Projeto ativo carregado: ID: {projetoAtivo.id}
        </p>
      ) : null}

      {mutation.isError ? (
        <p
          style={{
            marginTop: "16px",
            padding: "10px 12px",
            borderRadius: "8px",
            background: "#fee2e2",
            color: "#991b1b",
            fontWeight: 600,
          }}
        >
          Falha ao criar projeto: {mutation.error?.message || "erro desconhecido"}
        </p>
      ) : null}
    </section>
  );
}
