package domains.voz.java;

import android.content.Context;
import android.speech.tts.TextToSpeech;

import java.util.Locale;

public class TTS implements TextToSpeech.OnInitListener {

    private TextToSpeech tts;
    private boolean ready = false;

    public TTS(Context context) {
        tts = new TextToSpeech(context, this);
    }

    @Override
    public void onInit(int status) {
        if (status == TextToSpeech.SUCCESS) {
            tts.setLanguage(new Locale("pt", "BR"));
            ready = true;
        }
    }

    public boolean isReady() {
        return ready;
    }

    public void speak(String text) {

        if (!ready) {
            return;
        }

        tts.speak(
                text,
                TextToSpeech.QUEUE_ADD,
                null,
                "sapudo"
        );
    }

    public void stop() {

        if (tts != null) {
            tts.stop();
        }
    }

    public boolean isSpeaking() {

        if (tts == null) {
            return false;
        }

        return tts.isSpeaking();
    }

    public void shutdown() {

        if (tts != null) {
            tts.stop();
            tts.shutdown();
            tts = null;
        }

        ready = false;
    }
}