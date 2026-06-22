package domains.voz.java;

public class QwenBridge {

    static {
        System.loadLibrary("ggml");
        System.loadLibrary("ggml-base");
        System.loadLibrary("llama");
        System.loadLibrary("llama_jni");
    }

    private long nativeContext = 0;

    public native long loadModel(
        String modelPath,
        int nCtx
    );

    public native String generate(
        long contextPtr,
        String system,
        String prompt,
        int maxTokens
    );

    public native void release(
        long contextPtr
    );

    public boolean inicializar(
        String modelPath
    ) {
        if (nativeContext != 0)
            return true;

        nativeContext =
            loadModel(
                modelPath,
                2048
            );

        return nativeContext != 0;
    }

    public String generate(
        String system,
        String prompt
    ) {
        if (nativeContext == 0)
            return "Modelo não carregado";

        return generate(
            nativeContext,
            system,
            prompt,
            512
        );
    }

    public void encerrar() {

        if (nativeContext == 0)
            return;

        release(nativeContext);

        nativeContext = 0;
    }
}