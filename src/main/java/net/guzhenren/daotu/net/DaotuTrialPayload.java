package net.guzhenren.daotu.net;

import net.guzhenren.daotu.DaotuMod;
import net.guzhenren.daotu.DaotuTrialService;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.network.handling.IPayloadContext;

/** C2S：接取某个已解锁的试炼；进度与奖励不由客户端提供。 */
public record DaotuTrialPayload(int runId, int milestone, String trialId)
        implements CustomPacketPayload {
    public static final Type<DaotuTrialPayload> TYPE =
            new Type<>(ResourceLocation.fromNamespaceAndPath(DaotuMod.MODID, "trial"));

    public static final StreamCodec<RegistryFriendlyByteBuf, DaotuTrialPayload> STREAM_CODEC =
            StreamCodec.of(
                    (buf, payload) -> {
                        buf.writeVarInt(payload.runId());
                        buf.writeVarInt(payload.milestone());
                        buf.writeUtf(payload.trialId());
                    },
                    buf -> new DaotuTrialPayload(buf.readVarInt(),
                            buf.readVarInt(), buf.readUtf()));

    @Override
    public Type<? extends CustomPacketPayload> type() { return TYPE; }

    public static void handle(DaotuTrialPayload payload, IPayloadContext context) {
        context.enqueueWork(() -> {
            if (context.player() instanceof ServerPlayer player) {
                DaotuTrialService.accept(player, payload.runId(),
                        payload.milestone(), payload.trialId());
            }
        });
    }
}