#include <jni.h>
#include <string>
#include <vector>
#include <android/log.h>
#include "llama.h"

#define TAG "LLAMA_JNI"

#define LOGI(...) \
__android_log_print(ANDROID_LOG_INFO,TAG,__VA_ARGS__)

#define LOGE(...) \
__android_log_print(ANDROID_LOG_ERROR,TAG,__VA_ARGS__)

struct LlamaContext {
    llama_model* model;
    llama_context* ctx;
    llama_sampler* sampler;
};

// Helper manual para adicionar tokens ao batch (API C pura)
void batch_add(llama_batch & batch, llama_token id, llama_pos pos, const std::vector<llama_seq_id> & seq_ids, bool logits) {
    batch.token[batch.n_tokens] = id;
    batch.pos[batch.n_tokens] = pos;
    batch.n_seq_id[batch.n_tokens] = seq_ids.size();
    for (size_t i = 0; i < seq_ids.size(); ++i) {
        batch.seq_id[batch.n_tokens][i] = seq_ids[i];
    }
    batch.logits[batch.n_tokens] = logits;
    batch.n_tokens++;
}

extern "C"
JNIEXPORT jlong JNICALL
Java_domains_voz_java_QwenBridge_loadModel(
    JNIEnv* env,
    jobject,
    jstring modelPath,
    jint nCtx
) {

    const char* path =
        env->GetStringUTFChars(
            modelPath,
            nullptr
        );

    llama_backend_init();

    llama_model_params modelParams =
        llama_model_default_params();

    llama_model* model =
        llama_model_load_from_file(
            path,
            modelParams
        );

    LOGI("Retornou de llama_model_load_from_file");

    env->ReleaseStringUTFChars(
        modelPath,
        path
    );

    if (!model) {
        LOGE("llama_model_load_from_file retornou NULL");
        return 0;
    }

    LOGI("Modelo carregado");

    llama_context_params ctxParams =
        llama_context_default_params();

    ctxParams.n_ctx = nCtx;
    ctxParams.n_threads = 4;

    LOGI("Criando contexto");

    llama_context* ctx =
        llama_init_from_model(
            model,
            ctxParams
        );

    if (!ctx) {

        LOGE("llama_init_from_model retornou NULL");

        llama_model_free(model);

        return 0;
    }

    LOGI("Contexto criado");

    llama_sampler* sampler =
        llama_sampler_init_greedy();

    if (!sampler) {

        LOGE("llama_sampler_init_greedy retornou NULL");

        llama_free(ctx);
        llama_model_free(model);

        return 0;
    }

    LOGI("Sampler criado");

    auto* state =
        new LlamaContext{
            model,
            ctx,
            sampler
        };

    LOGI("LOAD OK");

    return reinterpret_cast<jlong>(
        state
    );
}

extern "C"
JNIEXPORT jstring JNICALL
Java_domains_voz_java_QwenBridge_generate__JLjava_lang_String_2Ljava_lang_String_2I(
    JNIEnv* env,
    jobject,
    jlong ptr,
    jstring system,
    jstring prompt,
    jint maxTokens
) {

    auto* state =
        reinterpret_cast<LlamaContext*>(ptr);

    if (!state)
        return env->NewStringUTF("");

    LOGI("GENERATE INICIO");

    llama_kv_cache_clear(state->ctx);

    const char* sys =
        env->GetStringUTFChars(
            system,
            nullptr
        );

    const char* usr =
        env->GetStringUTFChars(
            prompt,
            nullptr
        );

    std::string fullPrompt =
        "<|im_start|>system\n"
        + std::string(sys)
        + "<|im_end|>\n"
        "<|im_start|>user\n"
        + std::string(usr)
        + "<|im_end|>\n"
        "<|im_start|>assistant\n";

    env->ReleaseStringUTFChars(
        system,
        sys
    );

    env->ReleaseStringUTFChars(
        prompt,
        usr
    );

    std::vector<llama_token> tokens(
        fullPrompt.size() + 32
    );

    const llama_vocab * vocab =
        llama_model_get_vocab(
            state->model
        );

    int nTokens =
        llama_tokenize(
            vocab,
            fullPrompt.c_str(),
            fullPrompt.length(),
            tokens.data(),
            tokens.size(),
            true,
            true
        );

    if (nTokens <= 0) {
        return env->NewStringUTF("");
    }

    tokens.resize(nTokens);

    llama_batch batch =
        llama_batch_init(
            nTokens,
            0,
            1
        );

    for (int i = 0; i < nTokens; i++) {
        batch_add(
            batch,
            tokens[i],
            i,
            {0},
            i == nTokens - 1
        );
    }

    int rc =
        llama_decode(
            state->ctx,
            batch
        );

    if (rc != 0) {

        LOGE(
            "llama_decode falhou rc=%d nTokens=%d",
            rc,
            nTokens
        );

        llama_batch_free(batch);

        return env->NewStringUTF(
            "decode error"
        );
    }

    std::string result;

    int pos = nTokens;

    for (
        int i = 0;
        int(i) < int(maxTokens);
        i++
    ) {

        llama_token token =
            llama_sampler_sample(
                state->sampler,
                state->ctx,
                -1
            );

        if (
            llama_vocab_is_eog(
                vocab,
                token
            )
        )
            break;

        char piece[256];

        int len =
            llama_token_to_piece(
                vocab,
                token,
                piece,
                sizeof(piece),
                0,
                true
            );

        if (len > 0)
            result.append(
                piece,
                len
            );

        batch.n_tokens = 0; // "clear" o batch para o próximo token

        batch_add(
            batch,
            token,
            pos++,
            {0},
            true
        );

        if (
            llama_decode(
                state->ctx,
                batch
            ) != 0
        )
            break;
    }

    llama_batch_free(batch);

    return env->NewStringUTF(
        result.c_str()
    );
}

extern "C"
JNIEXPORT void JNICALL
Java_domains_voz_java_QwenBridge_release(
    JNIEnv*,
    jobject,
    jlong ptr
) {

    auto* state =
        reinterpret_cast<LlamaContext*>(
            ptr
        );

    if (!state)
        return;

    llama_sampler_free(
        state->sampler
    );

    llama_free(
        state->ctx
    );

    llama_model_free(
        state->model
    );

    delete state;

    llama_backend_free();
}